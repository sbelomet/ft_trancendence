import * as THREE from 'three';

import { FontLoader } from '/static/node_modules/three/examples/jsm/loaders/FontLoader.js';
import { RenderPass } from '/static/node_modules/three/examples/jsm/postprocessing/RenderPass.js';
import { OutputPass } from '/static/node_modules/three/examples/jsm/postprocessing/OutputPass.js';
import { ShaderPass } from '/static/node_modules/three/examples/jsm/postprocessing/ShaderPass.js';
import { TextGeometry } from '/static/node_modules/three/examples/jsm/geometries/TextGeometry.js';
import { OrbitControls } from '/static/node_modules/three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from '/static/node_modules/three/examples/jsm/postprocessing/EffectComposer.js';
import { UnrealBloomPass } from '/static/node_modules/three/examples/jsm/postprocessing/UnrealBloomPass.js';

import {
    lights,
    layers,
    cameraFov,
    boundaries,
    post_params,
    text_params
} from '../utils/game_utils.js';
import { canvasSize } from '../utils/functions_utils.js';

import Ball from './game_classes/Ball.js';
import Plane from './game_classes/Plane.js';
import Score from './game_classes/Score.js';
import Paddle from './game_classes/Paddle.js';

import managerStatus from './ManagerStatus.js';
import managerGame from './game_classes/ManagerGame.js';
import managerToast from './ManagerToast.js';
import managerState from './ManagerState.js';

export default class GameRender extends THREE.EventDispatcher {
    #end = false;
    #inTournament = false;
    #currentSize = undefined;
    #loaded_font = undefined;
    #primitives = {
        scene: undefined,
        camera: undefined,
        content: undefined,
        renderer: undefined,
        controls: undefined
    }
    #objects = {
        info: undefined,
        ball: undefined,
        plane: undefined,
        score1: undefined,
        score2: undefined,
        paddle_l: undefined,
        paddle_r: undefined
    }
    #composers = {
        mixPass: undefined,
        bloomPass: undefined,
        outputPass: undefined,
        renderScene: undefined,
        finalComposer: undefined,
        bloomComposer: undefined
    }
    #listeners = {
        keyup: this.#handleKeyUp.bind(this),
        resize : this.#handleResize.bind(this),
        keydown: this.#handleKeyDown.bind(this)
    }

    constructor() {
        super();
    }

    /* Setters-Getters */

    get getEnd() {
        return (this.#end);
    }

    get #getListeners() {
        return (this.#listeners);
    }

    get #getPrimitives() {
        return (this.#primitives);
    }

    get #getObjects() {
        return (this.#objects);
    }

    get #getComposers() {
        return (this.#composers);
    }

    get getInTournament() {
        return (this.#inTournament);
    }

    get #getCurrentSize() {
        return (this.#currentSize);
    }

    get #getLoadedFont() {
        return (this.#loaded_font);
    }

    /**
     * @param {Object} value
    */
    set #setLoadedFont(value) {
        this.#loaded_font = value;
    }

    /**
     * @param {Object} value
    */
    set #setCurrentSize(value) {
        this.#currentSize = value;
    }

    /**
     * @param {boolean} value
    */
    set #setInTournament(value) {
        this.#inTournament = value;
    }

    /**
     * @param {boolean} value
    */
    set #setEnd(value) {
        this.#end = value;
    }

    async init() {
        /* create utils */

        const loader = new FontLoader();
        this.#setLoadedFont = await loader.loadAsync(
            "/static/node_modules/three/examples/fonts/helvetiker_bold.typeface.json",
            function ( _xhr ) {
                //console.log( `font ${(xhr.loaded / xhr.total * 100)}% loaded` );
            }
        );

        new THREE.Layers().set( layers.BLOOM_SCENE );

        /* init primitives */

        this.#initPrimitives();

        /* init objects and adding to scene */

        this.#initObjects();

        /* init Composers */
    
        this.#initComposers();

        /* listeners */

        this.#addingEventListeners();
    }

    #initPrimitives() {
        /* Container */
        const content = document.getElementById("content");
        const wrapper = document.createElement("div");
        wrapper.setAttribute("class", "fill_div");
        const div = document.createElement("div");
        div.id = "canvas_parent";
        div.setAttribute("class", "h-100 d-flex justify-content-center align-items-center");

        wrapper.appendChild(div);
        content.appendChild(wrapper);
        this.#primitives.content = div;
        this.#setCurrentSize = canvasSize(div);
        
        /* Scene and adding lights */
        this.#primitives.scene = new THREE.Scene();
        this.#primitives.scene.add(...lights);

        /* Camera */
        this.#primitives.camera = new THREE.PerspectiveCamera(
            cameraFov, this.#currentSize.width/this.#currentSize.height, 0.1
        );
        this.#primitives.camera.position.set(80, 130, 80);

        /* Renderer */
        this.#primitives.renderer = new THREE.WebGLRenderer( { antialias: true } );
        this.#primitives.renderer.setPixelRatio( window.devicePixelRatio );
        this.#primitives.renderer.setSize( this.#currentSize.width, this.#currentSize.height );
        this.#primitives.renderer.toneMapping = THREE.ReinhardToneMapping;
        this.#primitives.content.appendChild(this.#primitives.renderer.domElement);

        /* Controls */
        this.#primitives.controls = new OrbitControls(
            this.#primitives.camera,
            this.#primitives.renderer.domElement
        );
        this.#primitives.controls.maxPolarAngle = Math.PI * 0.5;
        this.#primitives.controls.target = new THREE.Vector3(80, 0, 45);
        this.#primitives.controls.maxDistance = 150;
        this.#primitives.controls.minDistance = 1;
    }

    async #initObjects() {
        const scene = this.#getPrimitives.scene;
        const camera = this.#getPrimitives.camera;

        /* Plane */
        this.#objects.plane = new Plane(scene, boundaries);

        /* Paddles */
        this.#objects.paddle_l = new Paddle(
            scene,
            new THREE.Vector3(10, 0, 45)
        );
        this.#objects.paddle_r = new Paddle(
            scene,
            new THREE.Vector3(150, 0, 45)
        );

        /* Ball */
        this.#objects.ball = new Ball( scene );

        /* Scores */
        const score1 = new Score(
            this.#getLoadedFont,
            {
                scene: scene,
                camera: camera,
                name: "Score1",
                geometryText: "0",
                position: new THREE.Vector3(-10, 10, 45)
            }
        );
        score1.addEventListener("ongoal", (e) => {
            const newScore = parseInt(e.message);
            const geometry = this.#getScoreGeometry(newScore);

            score1.setScore = newScore;
            score1.getMesh.geometry = geometry;
            score1.getMesh.geometry.getAttribute('position').needsUpdate = true;
        });
        score1.addEventListener("ending", () => {
            const users = managerGame.getUsers;
            const finalScores = managerGame.getFinalScore;

            const text = finalScores.scores.player1 > finalScores.scores.player2 ? `${users.player1Name} wins!`
                : `${users.player2Name} wins!`;

            const geometry = new TextGeometry(text, {
                font: this.#getLoadedFont,
                ...text_params
            });
            geometry.center();

            score1.getMesh.geometry = geometry;
            score1.getMesh.position.copy(new THREE.Vector3(80, 10, 220))
            score1.getMesh.geometry.getAttribute('position').needsUpdate = true;

            this.#primitives.controls.target = new THREE.Vector3(80, 10, 220);
        });

        const score2 = new Score(
            this.#getLoadedFont,
            {
                scene: scene,
                camera: camera,
                name: "Score2",
                geometryText: "0",
                position: new THREE.Vector3(170, 10, 45)
            }
        );
        score2.addEventListener("ongoal", (e) => {
            const newScore = parseInt(e.message);
            const geometry = this.#getScoreGeometry(newScore);

            score2.setScore = newScore;
            score2.getMesh.geometry = geometry;
            score2.getMesh.geometry.getAttribute('position').needsUpdate = true;
        });

        const infoPlayers = new Score(
            this.#getLoadedFont,
            {
                scene: scene,
                camera: camera,
                name: "Players names",
                geometryText: `${managerGame.getUsers.player1Name} vs ${managerGame.getUsers.player2Name}`,
                position: new THREE.Vector3(80, 10, -25)
            }
        );

        this.#getObjects.score1 = score1;
        this.#getObjects.score2 = score2;
        this.#getObjects.info = infoPlayers;
    }

    #initComposers() {
        this.#composers.renderScene = new RenderPass( 
            this.#primitives.scene, 
            this.#primitives.camera 
        );

        this.#composers.bloomPass = new UnrealBloomPass( 
            new THREE.Vector2( this.#currentSize.width, this.#currentSize.height ), 1.5, 0.4, 0.85
        );
        this.#composers.bloomPass.threshold = post_params.threshold;
        this.#composers.bloomPass.strength = post_params.strength;
        this.#composers.bloomPass.radius = post_params.radius;

        this.#composers.bloomComposer = new EffectComposer( this.#primitives.renderer );
        this.#composers.bloomComposer.renderToScreen = false;
        this.#composers.bloomComposer.addPass(  this.#composers.renderScene );
        this.#composers.bloomComposer.addPass(  this.#composers.bloomPass );

        this.#composers.mixPass = new ShaderPass(
            new THREE.ShaderMaterial( {
                uniforms: {
                    baseTexture: { value: null },
                    bloomTexture: { value:  this.#composers.bloomComposer.renderTarget2.texture }
                },
                vertexShader: document.getElementById( 'vertexshader' ).textContent,
                fragmentShader: document.getElementById( 'fragmentshader' ).textContent,
                defines: {}
            } ), 'baseTexture'
        );
        this.#composers.mixPass.needsSwap = true;

        this.#composers.outputPass = new OutputPass();

        this.#composers.finalComposer = new EffectComposer( this.#primitives.renderer );
        this.#composers.finalComposer.addPass(  this.#composers.renderScene );
        this.#composers.finalComposer.addPass(  this.#composers.mixPass );
        this.#composers.finalComposer.addPass(  this.#composers.outputPass );
    }

    #isValidKey(key) {
        return (key === "w" || key === "s" || key === "ArrowUp" || key === "ArrowDown");
    }

    #isPlayer2(key) {
        return (key === "ArrowUp" || key === "ArrowDown");
    }

    #handleKeyDown(e) {
        if (this.#isValidKey(e.key) && managerGame.getHaveWebsocket) {
    
            let player = (this.#isPlayer2(e.key) && managerGame.getGameType === "local")
                ? "player2" : "player1";
            managerGame.action(e.key, player, "keydown");
        }
    };

    #handleKeyUp(e) {
        if (this.#isValidKey(e.key) && managerGame.getHaveWebsocket) {

            let player = (this.#isPlayer2(e.key) && managerGame.getGameType === "local")
                ? "player2" : "player1";
            managerGame.action(e.key, player, "keyup");
        }
    }

    #handleResize() {
        const content = document.getElementById("canvas_parent");
        this.#setCurrentSize = canvasSize(content);
        const sizes = this.#getCurrentSize;
        this.#primitives.camera.aspect = sizes.width / sizes.height;
        this.#primitives.camera.updateProjectionMatrix();
    
        this.#getPrimitives.renderer.setSize(sizes.width, sizes.height);
    
        this.#getComposers.bloomComposer.setSize( sizes.width, sizes.height );
        this.#getComposers.finalComposer.setSize( sizes.width, sizes.height );

        requestAnimationFrame(this.#tic.bind(this));
    }

    #addingEventListeners() {
        window.addEventListener("resize", this.#listeners.resize, false);
        document.addEventListener("keydown", this.#getListeners.keydown, false);
        document.addEventListener("keyup", this.#getListeners.keyup, false);
    }

    #removeEventListeners() {
        window.removeEventListener("resize", this.#getListeners.resize, false);
        document.removeEventListener("keydown", this.#getListeners.keydown, false);
        document.removeEventListener("keyup", this.#getListeners.keyup, false);
    }

    #removeGame(withScore = false) {
        if (withScore) {
            this.#getObjects.score1.finishGame();
            const id = managerState.getUserID;
            const finalScores = managerGame.getFinalScore;
            if (this.getInTournament && (id !== finalScores?.winnerId))
                this.dispatchEvent({ type: "toasts", message: "You can return to the hub" });
        }
        this.#removeEventListeners();
        managerGame.closeConnection();
        this.#setEnd = true;
    }

    #tic() {
        const state = managerGame.getState;

        const score1 = this.#getObjects.score1;
        const score2 = this.#getObjects.score2;

        if (managerGame.getIsEnded) {
            if (managerGame.getError) {
                this.#removeGame();
                managerToast.makeToast({
                    message: "Error while playing, returning to hub",
                    clickable: false,
                    toast_color: colorToast.red
                });
                this.dispatchEvent({ type: 'error' });
                return ;
            } else
                this.#removeGame(true);
        }

        this.#getObjects.ball.update(state.ball);

        this.#getObjects.paddle_l.update(state.players.player1);
        this.#getObjects.paddle_r.update(state.players.player2);

        if (state.scores.player1 != score1.getScore) {
            score1.updateScore(state.scores.player1);
        } else if (state.scores.player2 != score2.getScore) {
            score2.updateScore(state.scores.player2);
        }

        this.#getPrimitives.controls.update();

        score1.getMesh.lookAt( this.#primitives.camera.position );
        score2.getMesh.lookAt( this.#primitives.camera.position );

        this.#getComposers.bloomComposer.render();
        this.#getComposers.finalComposer.render();

        if (this.getEnd) {
            this.#primitives.controls.enable = false;
            this.#primitives.controls = undefined;
            this.dispatchEvent({ type: 'close' });
            return ;
        }

        requestAnimationFrame(this.#tic.bind(this));
    };

    #getScoreGeometry(score) {
        const geometry = new TextGeometry(`${score}`, {
            font: this.#getLoadedFont,
            ...text_params
        });
    
        geometry.center();
    
        return (geometry);
    };

    startGame() {
        try {
            if (!managerGame.getHaveWebsocket)
                throw new Error ("No websocket instance");
            this.#setInTournament = managerGame.getIsTournament;
            requestAnimationFrame(this.#tic.bind(this));
        } catch (error) {
            managerStatus.handleErrorResponse(404, error, true);
        }
    };
};