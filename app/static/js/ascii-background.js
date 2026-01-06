import * as THREE from 'three';
import { AsciiEffect } from 'three/addons/effects/AsciiEffect.js';

// Theme color configurations
const themes = {
    dark: {
        background: 0x0a0a0a,
        textColor: '#404040',
        bgColor: '#0a0a0a',
        particleColor: 0xffffff
    },
    light: {
        background: 0xffffff,
        textColor: '#d0d0d0',
        bgColor: '#ffffff',
        particleColor: 0x000000
    }
};

let currentEffect = null;
let currentScene = null;
let currentParticles = null;

export function updateAsciiTheme(isDark) {
    if (!currentEffect || !currentScene) return;

    const theme = isDark ? themes.dark : themes.light;
    currentScene.background = new THREE.Color(theme.background);
    currentEffect.domElement.style.color = theme.textColor;
    currentEffect.domElement.style.backgroundColor = theme.bgColor;

    // Update particle colors
    if (currentParticles) {
        currentParticles.children.forEach((particle) => {
            particle.material.color.setHex(theme.particleColor);
        });
    }
}

export function initAsciiBackground(containerId = 'ascii-background', isDark = true) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Don't reinitialize if already exists
    if (container.children.length > 0) return;

    const theme = isDark ? themes.dark : themes.light;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(theme.background);
    currentScene = scene;

    const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.z = 500;

    const renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);

    // ASCII Effect
    const effect = new AsciiEffect(renderer, ' .:-=+*#%@', { invert: true });
    effect.setSize(window.innerWidth, window.innerHeight);
    effect.domElement.style.color = theme.textColor;
    effect.domElement.style.backgroundColor = theme.bgColor;
    effect.domElement.style.position = 'absolute';
    effect.domElement.style.top = '0';
    effect.domElement.style.left = '0';
    effect.domElement.style.zIndex = '1';
    effect.domElement.style.pointerEvents = 'none';
    currentEffect = effect;

    // Add to DOM
    container.appendChild(effect.domElement);

    // Create particle cloud
    const particleCount = 250;
    const particles = new THREE.Group();
    currentParticles = particles;

    for (let i = 0; i < particleCount; i++) {
        const geometry = new THREE.SphereGeometry(3, 8, 8);
        const material = new THREE.MeshBasicMaterial({ color: theme.particleColor });
        const sphere = new THREE.Mesh(geometry, material);

        // Random position in 3D space
        sphere.position.x = (Math.random() - 0.5) * 1000;
        sphere.position.y = (Math.random() - 0.5) * 600;
        sphere.position.z = (Math.random() - 0.5) * 600;

        // Store initial position for animation
        sphere.userData.initialX = sphere.position.x;
        sphere.userData.initialY = sphere.position.y;
        sphere.userData.initialZ = sphere.position.z;
        sphere.userData.speed = 0.5 + Math.random() * 1.5;
        sphere.userData.offset = Math.random() * Math.PI * 2;

        particles.add(sphere);
    }

    scene.add(particles);

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    // Animation
    let animationId;
    const clock = new THREE.Clock();

    function animate() {
        animationId = requestAnimationFrame(animate);

        const time = clock.getElapsedTime();

        // Animate each particle with wave-like motion
        particles.children.forEach((particle) => {
            const { initialX, initialY, initialZ, speed, offset } = particle.userData;

            // Drift motion with sine waves
            particle.position.x = initialX + Math.sin(time * speed * 0.3 + offset) * 30;
            particle.position.y = initialY + Math.cos(time * speed * 0.2 + offset) * 20;
            particle.position.z = initialZ + Math.sin(time * speed * 0.4 + offset * 2) * 25;
        });

        // Slow rotation of entire particle system
        particles.rotation.y = time * 0.02;
        particles.rotation.x = Math.sin(time * 0.1) * 0.05;

        effect.render(scene, camera);
    }

    // Handle window resize
    function onWindowResize() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        effect.setSize(window.innerWidth, window.innerHeight);
    }

    window.addEventListener('resize', onWindowResize);

    // Pause animation when tab is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            cancelAnimationFrame(animationId);
        } else {
            clock.start();
            animate();
        }
    });

    // Start animation
    animate();
}
