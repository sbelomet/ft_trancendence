from rest_framework import viewsets, permissions, status, serializers
from django.contrib.auth import get_user_model
from .models import CustomUser, Friendship
from .serializers import UserSerializer, FriendshipSerializer, RegisterSerializer, UserPublicSerializer, UserDetailSerializer, UserLoginSerializer
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from .permissions import IsFriendOrSelf, IsOwnerOrAdmin, IsFriendshipRecipientOrAdmin
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, NotFound
from django.shortcuts import redirect
from django.conf import settings
import requests
import pyotp
import urllib.parse
from .jwt_tools import generate_tokens, set_tokens_in_cookies
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from matchmaking.models import Player


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger = logging.getLogger('myapp')
# logger.info()

#select_related permet le lazy loading et récupère la requete SQL en une fois
#plutot que d'itérer dans toute la DB et faire autant de requetes
#Utilisé pour les relations de type ForeignKey et OneToOneField.
#pour les relations  ManyToManyField et ForeignKey inversé il faut utiliser
#prefetch_related qui va attacher chaque requete et renvoyer le resultat final en une fois
User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related(
        'friendships_sent__to_user',  # Prefetch friends where the user sent the request
        'friendships_received__from_user'  # Prefetch friends where the user received the request
        ).all()
    
    parser_classes = [MultiPartParser, FormParser]  # Add support for file uploads
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options'] 

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        if query:
            # Perform a case-insensitive search on the username
            queryset = queryset.filter(username__icontains=query)
        return queryset
	
    def get_serializer_class(self):
        if self.action == 'list':
            return UserPublicSerializer
        elif self.action == 'retrieve':
            if self.request.user == self.get_object():
                return UserDetailSerializer  # for own profile
            else:
                return UserPublicSerializer
        else:
            return UserSerializer

        
    def get_permissions(self):
        if self.action in ['list']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()
    
    def validate_and_update_nickname(self, user, nickname):
        """
        Validate and update the user's nickname in the Player profile.
        """
        logger.info("updating nickname")
        if nickname:
            if Player.objects.filter(nickname=nickname).exclude(user=user).exists():
                raise serializers.ValidationError({"detail":"This nickname is already in use by another player."})
            try:
                player = user.player_profile
                player.nickname = nickname
                player.save()
            except Player.DoesNotExist:
                raise serializers.ValidationError({"detail":"Player profile not found for this user."})
    
    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        
        nickname = request.data.get('nickname')
        if user.remote_user and (set(request.data.keys()) != {"nickname"}):
            return Response(
                {"detail": "Remote users are allowed to update only their nickname."},
                status=403,
            )
        
        if nickname:
            self.validate_and_update_nickname(user, nickname)

        response = super().partial_update(request, *args, **kwargs)

        user.refresh_from_db()

        # If TOTP is enabled, include the QR code URL in the response
        logger.info(f"Enable : {user.enable_2fa}, secret : {user.otp_secret}, request data: {request.data}")
        if user.enable_2fa == 'totp' and user.otp_secret:
            totp = pyotp.TOTP(user.otp_secret)
            logger.info("URL otp sent")
            response.data['otp_provisioning_url'] = totp.provisioning_uri(
                name=user.email,
                issuer_name="transcendance",
            )
        return response
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        logger.info("in update")
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    #voir les amis d'un ami
    #decorateur action permet de créer des vues par forcément liées à des opétations CRUD
	#detail=False ou True permet de créer une url de détail ou global /myviewset/custom_action/ ou /myviewset/<id>/custom_action/
    @action(detail=True, methods=['get'], permission_classes=[IsFriendOrSelf])
    def see_friend_friends(self, request, pk=None):
        user = self.get_object()
        friendships = Friendship.objects.filter(
        Q(from_user=user, has_rights=True, is_blocked=False) |
        Q(to_user=user, has_rights=True, is_blocked=False)
    ).select_related('from_user', 'to_user')

        friends = set()
        for friendship in friendships:
            if friendship.from_user == user:
                friends.add(friendship.to_user)
            else:
                friends.add(friendship.from_user)

        serializer = UserPublicSerializer(friends, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrAdmin])
    def see_blocked_users(self, request, pk=None):
        user = self.get_object()
        # On vérifie que l'user est bien le request.user ou un admin
        # => De toute façon, IsOwnerOrAdmin s’en occupe déjà

        friendships = Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            has_rights=True,
            is_blocked=True 
        ).select_related('from_user', 'to_user')

        blocked_list = set()
        for friendship in friendships:
            if friendship.from_user == user:
                blocked_list.add(friendship.to_user)
            else:
                blocked_list.add(friendship.from_user)

        serializer = UserPublicSerializer(blocked_list, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def status(self, request, pk=None):
        data = {}
        user = request.user
        profile = self.get_object()
        friendship = Friendship.objects.filter(
            from_user=user,to_user=profile
        ).first()
        rev_friendship = Friendship.objects.filter(
            from_user=profile,to_user=user
        ).first()
        profile_status = "user"
        if not friendship and not rev_friendship:
            pass
        elif not friendship and rev_friendship:
            profile_status = "pending"
        elif (friendship.is_blocked):
            profile_status = "blocking"
            if (friendship.has_rights):
                profile_status = "blocked"
        elif (friendship.has_rights):
            profile_status = "friend"
        else:
            profile_status = "sent"
        data['profile_status'] = profile_status
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def see_online(self, request, pk=None):
        connected = User.objects.filter(is_online=True).exclude(id=request.user.id)
        serializer = UserPublicSerializer(connected, many=True, context={'request': request})
        return Response(serializer.data)
    
class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = serializer.data

        if user.enable_2fa == 'totp':
            user.otp_secret = pyotp.random_base32()
            user.save(update_fields=['otp_secret'])
            # Generate QR code
            totp = pyotp.TOTP(user.otp_secret)
            otp_url = totp.provisioning_uri(name=user.email, issuer_name="transcendance")
            data['otp_provisioning_url'] = otp_url
            data['detail'] = "Scan the QR code with your authenticator app to complete access code setup."

        data['redirect_url'] = '/login/'
        
        #return redirect('login-user')
        return Response(data, status= status.HTTP_201_CREATED)
    
  
class UserLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        #print("UserLoginView: POST request received")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        #print(f"UserLoginView: User authenticated with ID {user.id}")
        data = serializer.data

        if user.enable_2fa and user.enable_2fa != 'none':
            return self.initiate_2fa(request, user)
            
        user.is_online = True
        user.save()

        #login(request, user)
        #print(f"UserLoginView: Generating tokens for user {user.id}")
        # Generate JWT tokens
        access_token, refresh_token = generate_tokens(user)
        
        # Debugging: print tokens to check
        #print(f"UserLoginView: Generated access_token: {access_token}")  # Debugging line
        #print(f"UserLoginView: Generated refresh_token: {refresh_token}") 

        user_serializer = UserSerializer(user)
        # data = user_serializer.data
        # data['success'] = True
        # data['user_id'] = user.id
        data.update(user_serializer.data)
        data["detail"] = "Login succesfull!"
        
        response = Response(data, status=status.HTTP_200_OK)
        
        # Set cookies with the generated tokens
        set_tokens_in_cookies(response, access_token, refresh_token)
        
        return response

    def initiate_2fa(self, request, user):
        otp_method = request.data.get('2fa_method', 'none')
        data={}
        #set OTP session flag to have access to otp/verif/ path via RestrictOTPAccessMiddleware
        request.session['otp_in_progress'] = True
        request.session['username'] = user.username

        if user.enable_2fa == 'email' or otp_method == 'email':
            user.send_otp_email()
            data['detail'] = "Access code sent to your email."
            data['method_2fa'] = "email"
        elif user.enable_2fa == "totp":
            data['detail'] = "Use your authenticator app to generate the access code."
            data['method_2fa'] = "totp"
        else:
            raise ValidationError('Invalid 2FA method!')
        
        data['redirect_url'] = f"/otp/?method_2fa={user.enable_2fa}"
        
        # Return a status indicating that OTP verification is pending, user is not yet online
        return Response(data, status=status.HTTP_202_ACCEPTED)

class UserLogoutView(generics.GenericAPIView):
    permission_classes = [IsOwnerOrAdmin]
    
    def post(self, request):
        #print("in logout View")
        data={}
        try:
            refresh_token = request.COOKIES.get('refresh')
            if refresh_token is None:
                data['detail'] = "Refresh token is missing."
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            #print("Found refresh token")
            token = RefreshToken(refresh_token)
            #print("Created new refresh token")
            request.user.is_online = False
            request.user.save(update_fields=['is_online'])
            #print("User set offline")
            token.blacklist()
            #print("Blacklisted refresh token")

            request.session.flush()
            
            data['detail'] = "Logout successful."
            data['redirect_url'] = "/pre_login/"
            # Prepare the response to clear cookies
            response = Response(status=status.HTTP_205_RESET_CONTENT)

            response.set_cookie('access', '', max_age=0, path='/')
            response.set_cookie('refresh', '', max_age=0, path='/')
            response.delete_cookie('sessionid', path='/')

            #response = Response(data, status=status.HTTP_205_RESET_CONTENT, content_type="application/json")
            return response
        except Exception as e:
            data['detail'] = "Logout failed."
            return Response(data, status= status.HTTP_400_BAD_REQUEST)

class FriendshipViewSet(viewsets.ModelViewSet):
    queryset = Friendship.objects.select_related('from_user', 'to_user').all()
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options'] 

    def perform_create(self, serializer):
        is_blocked_request = self.request.data.get('is_blocked', 'False').lower() == 'true'
        from_user = self.request.user
        to_user = serializer.validated_data['to_user']

        existing = Friendship.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).first()

        if is_blocked_request:
            # BLOCAGE
            if existing:
                # -> "blocage d’un ami" ou d’une relation existante
                #    On met la row depuis from_user->to_user
                #    en blocked=True, rights=True 
                #    => le signal mettra la row inverse en blocked=True, rights=False
                #    => l’autre perd l’amitié
                existing.is_blocked = True
                existing.has_rights = True
                existing.save()
                serializer.instance = existing
                return
            else:
                # -> blocage à froid : on crée la row 
                #    => signal crée row inverse is_blocked=True, has_rights=False
                serializer.save(from_user=from_user, is_blocked=True, has_rights=True)
                return
        else:
            # DEMANDE AMI
            if existing:
                raise ValidationError({"detail":"A relationship already exists between you."})
            # => on crée la row : blocked=False, rights=False
            serializer.save(from_user=from_user, is_blocked=False, has_rights=False)

    @action(detail=True, methods=['put'], permission_classes=[IsFriendshipRecipientOrAdmin])
    def accept_friendship(self, request, pk=None):
        friendship = self.get_object()
        if friendship.has_rights:
            return Response({"detail": "You are already friends with this user."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # On suppose ici que c'est une "demande d'ami" => blocked=False, rights=False
        if friendship.is_blocked:
            return Response({"detail": "Cannot accept a friend request that is blocked."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Acceptation
        friendship.has_rights = True
        friendship.is_blocked = False
        friendship.save()

        return Response({"detail": "Friend request accepted successfully."}, 
                        status=status.HTTP_200_OK)
  
    @action(detail=True, methods=['put'], permission_classes=[IsFriendshipRecipientOrAdmin])
    def refuse_friendship(self, request, pk=None):
        friendship = self.get_object()
        if friendship.has_rights:
            return Response({"detail": "You are already friends with this user2."}, status=status.HTTP_400_BAD_REQUEST)
        if not friendship.is_blocked:
            friendship.delete()
            return Response({"detail": "Friendship request refused by the user."}, status=status.HTTP_200_OK)
        return Response({"detail": "Friendship entry is blocking the to_user and cannot be accepted."}, status=status.HTTP_400_BAD_REQUEST)
    
    # @action(detail=True, methods=['delete'], permission_classes=[IsOwnerOrAdmin])
    # def delete_friendship(self, request, pk=None):
    #     friendship = self.get_object()

    #     # Ensure the friendship is rights before deleting
    #     if not friendship.has_rights:
    #         return Response({"detail": "You are not friends with this user."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Fetch both the forward and reverse friendship entries
    #     from_user = friendship.from_user
    #     to_user = friendship.to_user

    #     # Delete both the entries
    #     Friendship.objects.filter(
    #         Q(from_user=from_user, to_user=to_user) |
    #         Q(from_user=to_user, to_user=from_user)
    #     ).delete()

    #     return Response({"detail": "The friendship has been successfully deleted."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def block(self, request, pk=None):
        from_user = request.user
        try:
            if (not pk.isdigit()):
                raise NotFound({"detail": "Numeric value expected for id."})
            to_user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if (from_user == to_user):
            return Response({"detail": "User cannot block or unblock himself."}, 
                        status=status.HTTP_400_BAD_REQUEST)

        # On essaie de récupérer la row from_user->to_user (get_or_create triggers signal with wrong values if create)
        friendship = Friendship.objects.filter(
            from_user=from_user,
            to_user=to_user
        ).first()
        
        if not friendship:
        # Create friendship manually
            friendship = Friendship(
                from_user=from_user,
                to_user=to_user,
                is_blocked=True,
                has_rights=True
            )
        else:
            friendship.is_blocked = True
            friendship.has_rights = True

        friendship.save()

        return Response({"detail": f"{to_user.username} has been blocked."}, 
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unblock(self, request, pk=None):
        from_user = request.user
        try:
            if (not pk.isdigit()):
                raise NotFound({"detail": "Numeric value expected for id."})
            to_user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if (from_user == to_user):
            return Response({"detail": "User cannot block or unblock himself."}, 
                        status=status.HTTP_400_BAD_REQUEST)

        friendship = Friendship.objects.filter(
            from_user=from_user, 
            to_user=to_user, 
            is_blocked=True
        ).first()

        if not friendship or not friendship.has_rights:
            return Response({"detail": "This user is not blocked by you."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
		# unblocking deletes relations in the friendships table
        Friendship.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).delete()
        return Response({"detail": f"You have unblocked {to_user.username}, you are not friends."},
                        status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['accept_friendship', 'refuse_friendship']:
            permission_classes = [IsFriendshipRecipientOrAdmin]
        else:
            permission_classes = [IsOwnerOrAdmin]
        return [permission() for permission in permission_classes]

class OTPVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        #print("in OTP View")

        # Retrieve username and OTP from session and request
        username = request.session.get('username')
        #username_data = request.data.get('username')
        otp = request.data.get('code')
        otp_method = request.data.get('2fa_method')
        #print(f"otp_in_progress: {request.session.get('otp_in_progress')}")

        # Validate required fields

        if not username:
            return Response({"detail": "Username required."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Retrieve user and validate existence
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "Invalid username."}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        
        if otp_method == "email":
            user.send_otp_email()
            return Response({"detail": "Access code sent to your email."}, status=status.HTTP_202_ACCEPTED)
        
        if not otp:
            return Response({"detail": "OTP required."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        if user.enable_2fa == 'none':
            return Response({"detail": "2FA is not enabled for this user."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate OTP
        if not user.validate_otp(otp):
            return Response({"detail": "Invalid OTP."}, 
                        status=status.HTTP_400_BAD_REQUEST)

        # OTP valid, update user status and generate tokens
        user.is_online = True
        user.save()

        request.session['otp_in_progress'] = False

        # Generate JWT tokens
        access_token, refresh_token = generate_tokens(user)

        # Serialize user data and return response
        user_serializer = UserSerializer(user)
        data = user_serializer.data
        data['detail'] = "OTP verification successful."      

        response = Response(data, status=status.HTTP_200_OK)

        # Set JWT tokens in cookies
        set_tokens_in_cookies(response, access_token, refresh_token)

        return response
    

#token_urlsafe generates a cutom token and controll it to avoid cross site request forgery
#stocks it in the user session
#construction of the url with the correct params
#urllib.parse.urlencode(params) function transforms dictonary
#in encoded request url like 'client_id=myclient&redirect_uri=http%3A%2F%2Fexample.com%2Fcallback'
@api_view(['GET'])
@authentication_classes([])  # Disable authentication
@permission_classes([AllowAny])  # Allow access to anyone
def redirect_to_42(request):
    authorization_url = settings.OAUTH2_AUTHORIZATION_URL

    params = {
        'client_id': settings.OAUTH2_CLIENT_ID,
        'redirect_uri': settings.OAUTH2_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'public',
        'state': settings.OAUTH2_STATE,
    }
    
    url = f"{authorization_url}?{urllib.parse.urlencode(params)}"
    
    return Response({"redirect_url": url})


#the code received from request to the OAuth2 is used as a tradeof for later exchange (post)

class Callback42View(APIView):
    authentication_classes = []  # disable class et permissions to allow extrnal check
    permission_classes = [] 

    def get(self, request):
        data = {}
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        
        if error:
            response = redirect(f"/?error={error}")
            response['Cache-Control'] = 'no-store'
            return response
        if not code:
            return Response({'error': 'Code or state not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not state:
            return Response({'error': 'State  not provided'}, status=status.HTTP_400_BAD_REQUEST)

        if state != settings.OAUTH2_STATE:
            return Response({'error': 'Invalid state parameter'}, status=status.HTTP_400_BAD_REQUEST)

        # exchange the code for an access token via post
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.OAUTH2_REDIRECT_URI,
            'client_id': settings.OAUTH2_CLIENT_ID,
            'client_secret': settings.OAUTH2_CLIENT_SECRET,
        }
        token_response = requests.post(settings.OAUTH2_TOKEN_URL, data=token_data)

        if token_response.status_code != 200:
            return ValidationError("Token exchange failed")


        token_json = token_response.json()
        access_token = token_json.get('access_token')

        # user infos is done by a request get made on the secure url given by
        #OAuth2 provider only accessible with a valid token
        user_info_response = requests.get(
            settings.OAUTH2_USER_INFO_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if user_info_response.status_code != 200:
            return Response({'error': 'Failed to retrieve user info'}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()
        
        # Check if the email already exists in the database
        existing_user = CustomUser.objects.filter(email=user_info.get('email')).first()
        
        if existing_user:
            if existing_user.username != user_info.get('login'):
                response = redirect(f"/register/?error=Email already in use. Please register with a different email.")
                response['Cache-Control'] = 'no-store'
                return response

            if not existing_user.remote_user:
                response = redirect(f"/register/?error=Cretentials already in use. Please register with different credentials.")
                response['Cache-Control'] = 'no-store'
                return response
           

        # Check if the username already exists in the database
        elif CustomUser.objects.filter(username=user_info.get('login')).exists():
            response = redirect(f"/register/?error=Username already in use. Please register with a different username.")
            response['Cache-Control'] = 'no-store'
            return response
        # If no conflicts, proceed to create or get the user
        user, created = CustomUser.objects.get_or_create(
            email=user_info.get('email'),
            defaults={
                'username': user_info.get('login'),
                'avatar': user_info.get('image', {}).get('versions', {}).get('medium'),
                'remote_user': True
            }
        )

        user.is_online = True
        user.save()

        access_token_jwt, refresh_token_jwt = generate_tokens(user)

        # Create response and set tokens in cookies
        response = redirect('/')  # mettre ou ne pas mettre ca, telle est la question
        response['Cache-Control'] = 'no-store'
        set_tokens_in_cookies(response, access_token_jwt, refresh_token_jwt)
        return response