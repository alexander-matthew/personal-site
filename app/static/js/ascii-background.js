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

// Weather-specific particle behaviors
const weatherConfigs = {
    sunny: {
        speedMultiplier: 0.5,
        verticalDrift: 0.3,      // Gentle upward drift (heat shimmer)
        horizontalDrift: 0.1,
        rotationSpeed: 0.01,
        particleScale: 1,
        density: 1,
        chaos: 0
    },
    cloudy: {
        speedMultiplier: 0.3,
        verticalDrift: 0,
        horizontalDrift: 0.8,    // Slow horizontal drift
        rotationSpeed: 0.015,
        particleScale: 1.2,
        density: 1.2,
        chaos: 0.1
    },
    rainy: {
        speedMultiplier: 1.5,
        verticalDrift: -2,       // Falling down
        horizontalDrift: 0.3,
        rotationSpeed: 0.02,
        particleScale: 0.8,
        density: 1.5,
        chaos: 0.2
    },
    stormy: {
        speedMultiplier: 3,
        verticalDrift: -2.5,
        horizontalDrift: 1.5,    // Strong wind
        rotationSpeed: 0.08,
        particleScale: 0.7,
        density: 2,
        chaos: 0.8              // High chaos for lightning-like bursts
    },
    snowy: {
        speedMultiplier: 0.4,
        verticalDrift: -0.5,     // Gentle snowfall
        horizontalDrift: 0.4,    // Wind-blown snow
        rotationSpeed: 0.03,
        particleScale: 0.9,
        density: 1.3,
        chaos: 0.1
    },
    foggy: {
        speedMultiplier: 0.2,
        verticalDrift: 0,
        horizontalDrift: 0.2,
        rotationSpeed: 0.005,
        particleScale: 1.5,
        density: 0.8,           // Less particles but larger
        chaos: 0
    }
};

let currentEffect = null;
let currentScene = null;
let currentParticles = null;
let currentWeather = null;
let targetWeather = null;
let weatherTransition = 0;

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

// Update weather mode for ASCII background
export function updateAsciiWeather(weatherTheme) {
    if (!weatherConfigs[weatherTheme]) return;

    targetWeather = weatherTheme;
    weatherTransition = 0; // Start transition
}

// Get interpolated weather config during transitions
function getWeatherConfig() {
    if (!currentWeather || !targetWeather || currentWeather === targetWeather) {
        return weatherConfigs[targetWeather || currentWeather || 'sunny'];
    }

    // Interpolate between current and target weather
    const from = weatherConfigs[currentWeather];
    const to = weatherConfigs[targetWeather];
    const t = weatherTransition;

    return {
        speedMultiplier: from.speedMultiplier + (to.speedMultiplier - from.speedMultiplier) * t,
        verticalDrift: from.verticalDrift + (to.verticalDrift - from.verticalDrift) * t,
        horizontalDrift: from.horizontalDrift + (to.horizontalDrift - from.horizontalDrift) * t,
        rotationSpeed: from.rotationSpeed + (to.rotationSpeed - from.rotationSpeed) * t,
        particleScale: from.particleScale + (to.particleScale - from.particleScale) * t,
        density: from.density + (to.density - from.density) * t,
        chaos: from.chaos + (to.chaos - from.chaos) * t
    };
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

        // Get current weather config (with smooth transitions)
        const weather = getWeatherConfig();

        // Update weather transition
        if (targetWeather && currentWeather !== targetWeather) {
            weatherTransition += 0.02; // Smooth transition over ~2.5 seconds
            if (weatherTransition >= 1) {
                weatherTransition = 1;
                currentWeather = targetWeather;
            }
        }

        // Animate each particle with weather-aware motion
        particles.children.forEach((particle) => {
            const { initialX, initialY, initialZ, speed, offset } = particle.userData;

            // Weather-modified speed
            const weatherSpeed = speed * weather.speedMultiplier;

            // Calculate base drift position with weather effects
            let baseX = initialX + Math.sin(time * weatherSpeed * 0.3 + offset) * 30;
            let baseY = initialY + Math.cos(time * weatherSpeed * 0.2 + offset) * 20;
            let baseZ = initialZ + Math.sin(time * weatherSpeed * 0.4 + offset * 2) * 25;

            // Apply weather-specific drift
            baseY += time * weather.verticalDrift * 10;
            baseX += time * weather.horizontalDrift * 5;

            // Wrap particles that go out of bounds (for continuous rain/snow effect)
            if (weather.verticalDrift < 0) {
                // Falling particles - wrap from bottom to top
                const wrapY = ((baseY + 400) % 800) - 400;
                baseY = wrapY;
            } else if (weather.verticalDrift > 0) {
                // Rising particles - wrap from top to bottom
                const wrapY = (((baseY - 400) % 800) + 800) % 800 - 400;
                baseY = wrapY;
            }

            // Horizontal wrapping
            if (Math.abs(weather.horizontalDrift) > 0.1) {
                const wrapX = ((baseX + 600) % 1200) - 600;
                baseX = wrapX;
            }

            // Add chaos (stormy weather random bursts)
            if (weather.chaos > 0 && Math.random() < weather.chaos * 0.02) {
                particle.userData.displaceX += (Math.random() - 0.5) * weather.chaos * 50;
                particle.userData.displaceY += (Math.random() - 0.5) * weather.chaos * 50;
            }

            // Calculate distance from mouse (in screen-projected space)
            const dx = baseX - mouse.worldX;
            const dy = baseY - mouse.worldY;
            const distance = Math.sqrt(dx * dx + dy * dy);

            // Apply ripple push if within radius
            if (distance < ripple.radius && distance > 0) {
                const force = (1 - distance / ripple.radius) * ripple.strength;
                const pushX = (dx / distance) * force;
                const pushY = (dy / distance) * force;
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

            // Update particle scale based on weather
            const targetScale = weather.particleScale;
            particle.scale.setScalar(particle.scale.x + (targetScale - particle.scale.x) * 0.05);
        });

        // Weather-modified rotation
        particles.rotation.y = time * weather.rotationSpeed;
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

    // Listen for weather change events from weather dashboard
    window.addEventListener('weatherchange', (event) => {
        const { theme } = event.detail;
        if (theme && weatherConfigs[theme]) {
            targetWeather = theme;
            weatherTransition = 0;
        }
    });

    // Start animation
    animate();
}
