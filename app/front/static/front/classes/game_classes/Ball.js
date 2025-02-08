import {
    Mesh,
    Color,
    SphereGeometry,
    MeshBasicMaterial,
} from 'three';

import { layers } from '../../utils/game_utils.js';

export default class Ball {

    constructor( scene ) {

        this.radius = 1.5;

        const color = new Color();
        color.setHSL( Math.random(), 0.7, Math.random() * 0.2 + 0.05 );

        this.geometry = new SphereGeometry( this.radius );
        this.material = new MeshBasicMaterial({ color: color });
        this.mesh = new Mesh( this.geometry, this.material );
        this.mesh.name = "Ball";

        this.mesh.layers.enable( layers.BLOOM_SCENE );

        scene.add(this.mesh);
    }

    update(pos) {
        this.mesh.position.x = (pos.x);
        this.mesh.position.z = (pos.y);
    }
}