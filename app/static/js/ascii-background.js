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

// Weather-specific particle behaviors with distinct motion patterns
const weatherConfigs = {
    sunny: {
        motionType: 'shimmer',   // Gentle heat shimmer effect
        waveAmplitude: 30,       // How much particles wave side-to-side
        waveSpeed: 0.3,          // Speed of wave motion
        fallSpeed: 0,            // No falling
        windSpeed: 0,            // No wind
        rotationSpeed: 0.015,
        particleScale: 1,
        chaos: 0
    },
    partlycloudy: {
        motionType: 'billow',    // Billowing cloud effect
        waveAmplitude: 50,       // Larger waves
        waveSpeed: 0.15,         // Slower, more majestic
        fallSpeed: 0,
        windSpeed: 0.3,          // Slight drift
        rotationSpeed: 0.01,
        particleScale: 1.1,
        chaos: 0
    },
    cloudy: {
        motionType: 'billow',    // Big billowing clouds
        waveAmplitude: 80,       // Large wave motion
        waveSpeed: 0.1,          // Very slow, cloud-like
        fallSpeed: 0,
        windSpeed: 0.5,          // Drifting
        rotationSpeed: 0.008,
        particleScale: 1.3,
        chaos: 0.05
    },
    rainy: {
        motionType: 'rain',      // Rain streaks
        waveAmplitude: 5,        // Minimal wave - mostly straight down
        waveSpeed: 0.5,
        fallSpeed: 8,            // Fast falling
        windSpeed: 1,            // Some wind
        rotationSpeed: 0.02,
        particleScale: 0.7,
        chaos: 0.1
    },
    stormy: {
        motionType: 'rain',      // Heavy rain
        waveAmplitude: 10,
        waveSpeed: 0.8,
        fallSpeed: 12,           // Very fast falling
        windSpeed: 4,            // Strong wind
        rotationSpeed: 0.05,
        particleScale: 0.6,
        chaos: 0.5               // Chaotic bursts
    },
    snowy: {
        motionType: 'snow',      // Gentle snowfall
        waveAmplitude: 40,       // Swaying motion
        waveSpeed: 0.2,
        fallSpeed: 1.5,          // Gentle falling
        windSpeed: 0.8,          // Wind-blown
        rotationSpeed: 0.02,
        particleScale: 0.9,
        chaos: 0.05
    },
    foggy: {
        motionType: 'billow',    // Slow fog drift
        waveAmplitude: 60,
        waveSpeed: 0.05,         // Very slow
        fallSpeed: 0,
        windSpeed: 0.2,
        rotationSpeed: 0.003,
        particleScale: 1.5,
        chaos: 0
    }
};

let currentEffect = null;
let currentScene = null;
let currentParticles = null;
let currentWeather = 'sunny';  // Default weather state
let targetWeather = 'sunny';
let weatherTransition = 1;     // Start fully transitioned

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
        motionType: t > 0.5 ? to.motionType : from.motionType,  // Switch halfway
        waveAmplitude: from.waveAmplitude + (to.waveAmplitude - from.waveAmplitude) * t,
        waveSpeed: from.waveSpeed + (to.waveSpeed - from.waveSpeed) * t,
        fallSpeed: from.fallSpeed + (to.fallSpeed - from.fallSpeed) * t,
        windSpeed: from.windSpeed + (to.windSpeed - from.windSpeed) * t,
        rotationSpeed: from.rotationSpeed + (to.rotationSpeed - from.rotationSpeed) * t,
        particleScale: from.particleScale + (to.particleScale - from.particleScale) * t,
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

            let baseX, baseY, baseZ;

            // Different motion patterns based on weather type
            switch (weather.motionType) {
                case 'rain':
                    // Rain: fast downward streaks with slight angle from wind
                    baseX = initialX + Math.sin(offset) * weather.waveAmplitude * 0.3;
                    baseX += time * weather.windSpeed * 20;  // Wind pushes rain sideways
                    baseY = initialY - (time * weather.fallSpeed * 30);  // Fast falling
                    baseY += Math.sin(time * weather.waveSpeed + offset) * weather.waveAmplitude * 0.2;
                    baseZ = initialZ;
                    break;

                case 'snow':
                    // Snow: gentle falling with swaying side-to-side motion
                    baseX = initialX + Math.sin(time * weather.waveSpeed * 2 + offset) * weather.waveAmplitude;
                    baseX += time * weather.windSpeed * 10;  // Wind drift
                    baseY = initialY - (time * weather.fallSpeed * 20);  // Gentle falling
                    baseZ = initialZ + Math.cos(time * weather.waveSpeed + offset * 2) * 20;
                    break;

                case 'billow':
                    // Clouds/Fog: large slow billowing waves
                    baseX = initialX + Math.sin(time * weather.waveSpeed + offset) * weather.waveAmplitude;
                    baseX += time * weather.windSpeed * 15;  // Slow drift
                    baseY = initialY + Math.cos(time * weather.waveSpeed * 0.7 + offset * 0.5) * weather.waveAmplitude * 0.5;
                    baseZ = initialZ + Math.sin(time * weather.waveSpeed * 0.5 + offset * 2) * 30;
                    break;

                case 'shimmer':
                default:
                    // Sunny: gentle heat shimmer rising
                    baseX = initialX + Math.sin(time * weather.waveSpeed + offset) * weather.waveAmplitude;
                    baseY = initialY + Math.cos(time * weather.waveSpeed * 0.8 + offset) * weather.waveAmplitude * 0.7;
                    baseY += time * 5;  // Gentle upward drift
                    baseZ = initialZ + Math.sin(time * weather.waveSpeed * 1.2 + offset * 2) * 25;
                    break;
            }

            // Wrap particles that go out of bounds
            if (weather.fallSpeed > 0 || weather.motionType === 'shimmer') {
                baseY = ((baseY % 800) + 800) % 800 - 400;
            }
            if (weather.windSpeed > 0) {
                baseX = ((baseX % 1200) + 1200) % 1200 - 600;
            }

            // Add chaos (stormy weather random bursts)
            if (weather.chaos > 0 && Math.random() < weather.chaos * 0.02) {
                particle.userData.displaceX += (Math.random() - 0.5) * weather.chaos * 80;
                particle.userData.displaceY += (Math.random() - 0.5) * weather.chaos * 80;
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
    console.log('[ASCII Background] Registering weatherchange event listener');
    window.addEventListener('weatherchange', (event) => {
        const { theme } = event.detail;
        console.log('[ASCII Background] Weather change event received:', theme);
        if (theme && weatherConfigs[theme]) {
            targetWeather = theme;
            weatherTransition = 0;
            console.log('[ASCII Background] Transitioning to weather:', theme, weatherConfigs[theme]);
        }
    });

    // Start animation
    animate();
}
