import {
    Vector2,
    AmbientLight
} from 'three';

/* Lights */

const amblightLight = new AmbientLight(0xffffff, 0.6);
amblightLight.name = "ambientLight";
const lights = [amblightLight];

/* Color params */

const color_params = {
    scoreColor: 0xdf740c,
    planeColor: 0xdbdbdb,
    paddleColor: 0x3633ff,
};

/* Text params */

const text_params = {
    size: 10,
    depth: 1.5,
    bevelOffset: 0,
    bevelSize: 0.05,
    bevelSegments: 5,
    curveSegments: 12,
    bevelEnabled: true,
    bevelThickness: 0.1
};

/* Post params */

const post_params = {
    threshold: 0,
    strength: 1,
    radius: 0.2,
    exposure: 1
};

/* Layers */

const layers = {
    BLOOM_SCENE: 1
};

/* Positions */

const boundaries = new Vector2(160, 90);

/* Camera settings */ 

const cameraFov = 75;

/* Score */

export {
    lights,
    layers,
    cameraFov,
    boundaries,
    post_params,
    text_params,
    color_params
};