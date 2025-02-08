import {
    LineSegments,
    PlaneGeometry,
    EdgesGeometry,
    LineBasicMaterial
} from 'three';

import { color_params } from '../../utils/game_utils.js';

export default class Plane {
    constructor( scene, boundaries ) {
        const planeGeometry = new PlaneGeometry(
            boundaries.x,
            boundaries.y,
            1,
            1
        );
        planeGeometry.rotateX(-Math.PI * 0.5);
        const edges = new EdgesGeometry( planeGeometry );
        this.lines = new LineSegments( edges, new LineBasicMaterial({
            color:color_params.planeColor
        }));
        this.lines.name = "boundaries";
        this.lines.position.set(80, 0, 45);
        scene.add( this.lines );
    }
};