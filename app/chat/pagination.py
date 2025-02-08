from rest_framework.pagination import PageNumberPagination
from urllib.parse import urlparse, urlunparse

class CustomPagination(PageNumberPagination):
	page_size = 10

	def get_paginated_response(self, data):
		response = super().get_paginated_response(data)
		response.data['next'] = self.remove_scheme_and_domain(response.data.get('next'))
		response.data['previous'] = self.remove_scheme_and_domain(response.data.get('previous'))
		return response

	def remove_scheme_and_domain(self, url):
		if url:
			parsed_url = urlparse(url)
			# Reconstruct the URL without the scheme and netloc
			url = urlunparse(('', '', parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
		return url