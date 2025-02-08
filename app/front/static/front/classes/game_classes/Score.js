import { MeshStandardMaterial, EventDispatcher, Mesh } from "three";

import { color_params, text_params, layers } from "../../utils/game_utils.js";

import { TextGeometry } from '/static/node_modules/three/examples/jsm/geometries/TextGeometry.js';

class Score extends EventDispatcher {
    #score = 0;
    #mesh = undefined;

    constructor( loadedFont, info ) {
        super();

        const GEOMETRY = new TextGeometry(info.geometryText, {
            font: loadedFont,
            ...text_params
        });
        const MATERIAL = new MeshStandardMaterial({
            color: color_params.scoreColor
        });
        GEOMETRY.center();

        this.#setMesh = new Mesh(GEOMETRY, MATERIAL);
        this.#mesh.scale.setScalar(1.5);
        this.#mesh.position.copy(info.position);
        this.#mesh.name = info.name;
        this.#mesh.lookAt( info.camera.position );
        this.#mesh.layers.enable( layers.BLOOM_SCENE );

        info.scene.add( this.getMesh );
    }

    /**
     * @returns {number}
    */
    get getScore() {
        return (this.#score);
    }

    /**
     * @returns {Mesh}
    */
    get getMesh() {
        return (this.#mesh);
    }

    /**
     * @param {number} value
    */
    set setScore(value) {
        this.#score = value;
    }

    /**
     * @param {Mesh} value
    */
    set #setMesh(value) {
        this.#mesh = value;
    }

    updateScore(score) {
        this.dispatchEvent({ type: 'ongoal', message: `${score}` });
    }

    finishGame() {
        this.dispatchEvent({ type: 'ending' });
    }
}

export default Score;