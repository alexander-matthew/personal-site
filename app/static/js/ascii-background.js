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

// Mouse tracking for ripple effect
const mouse = {
    x: 0,
    y: 0,
    worldX: 0,
    worldY: 0
};

// Ripple configuration
const ripple = {
    radius: 150,      // How far the ripple extends
    strength: 40,     // How much particles are pushed
    falloff: 0.92     // How quickly displacement decays (0-1, higher = slower return)
};

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

        // Ripple displacement (will be animated)
        sphere.userData.displaceX = 0;
        sphere.userData.displaceY = 0;

        particles.add(sphere);
    }

    scene.add(particles);

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    // Mouse event handler
    function onMouseMove(event) {
        // Normalize mouse position to -1 to 1
        mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

        // Convert to world coordinates (approximate, for the z=0 plane)
        mouse.worldX = mouse.x * 500;
        mouse.worldY = mouse.y * 300;
    }

    window.addEventListener('mousemove', onMouseMove);

    // Animation
    let animationId;
    const clock = new THREE.Clock();

    function animate() {
        animationId = requestAnimationFrame(animate);

        const time = clock.getElapsedTime();

        // Animate each particle with wave-like motion + ripple displacement
        particles.children.forEach((particle) => {
            const { initialX, initialY, initialZ, speed, offset } = particle.userData;

            // Calculate base drift position
            const baseX = initialX + Math.sin(time * speed * 0.3 + offset) * 30;
            const baseY = initialY + Math.cos(time * speed * 0.2 + offset) * 20;
            const baseZ = initialZ + Math.sin(time * speed * 0.4 + offset * 2) * 25;

            // Calculate distance from mouse (in screen-projected space)
            const dx = baseX - mouse.worldX;
            const dy = baseY - mouse.worldY;
            const distance = Math.sqrt(dx * dx + dy * dy);

            // Apply ripple push if within radius
            if (distance < ripple.radius && distance > 0) {
                // Strength falls off with distance (inverse, like water ripples)
                const force = (1 - distance / ripple.radius) * ripple.strength;

                // Push direction (away from mouse)
                const pushX = (dx / distance) * force;
                const pushY = (dy / distance) * force;

                // Add to displacement (accumulates for smooth effect)
                particle.userData.displaceX += pushX * 0.1;
                particle.userData.displaceY += pushY * 0.1;
            }

            // Decay displacement over time (particles settle back)
            particle.userData.displaceX *= ripple.falloff;
            particle.userData.displaceY *= ripple.falloff;

            // Apply final position
            particle.position.x = baseX + particle.userData.displaceX;
            particle.position.y = baseY + particle.userData.displaceY;
            particle.position.z = baseZ;
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
