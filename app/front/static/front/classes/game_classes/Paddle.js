import {
    Mesh,
    BoxGeometry,
    MeshBasicMaterial,
} from 'three';

import { layers, color_params } from '../../utils/game_utils.js';

export default class Paddle {
    constructor (scene, position) {
        this.scene = scene;

        const GEOMETRY = new BoxGeometry(1.5, 15, 2);
        GEOMETRY.rotateX(Math.PI * 0.5);
        const MATERIAL = new MeshBasicMaterial({ color: color_params.paddleColor });

        this.mesh = new Mesh(GEOMETRY, MATERIAL);

        this.mesh.layers.enable( layers.BLOOM_SCENE );
        this.mesh.position.copy( position );
        this.mesh.name = "paddle";

        this.scene.add( this.mesh );
    }

    update(pos) {
        //console.log("update paddle: ", pos);
        this.mesh.position.z = (pos.y + 7.5);
    };
};