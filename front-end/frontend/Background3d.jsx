import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, Float, MeshDistortMaterial } from '@react-three/drei';

function AnimatedShape() {
  const meshRef = useRef();

  // Slowly rotate the shape on every frame
  useFrame((state, delta) => {
    meshRef.current.rotation.x += delta * 0.1;
    meshRef.current.rotation.y += delta * 0.15;
  });

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={2}>
      <mesh ref={meshRef} position={[0, 0, -2]} scale={1.5}>
        {/* A twisty, tubular shape */}
        <torusKnotGeometry args={[2, 0.6, 128, 32]} />
        
        {/* A shiny material with some distortion to make it look fluid */}
        <MeshDistortMaterial 
          color="#00ff66" /* Using your accent green */
          envMapIntensity={1} 
          clearcoat={1} 
          clearcoatRoughness={0.1} 
          metalness={0.2}
          roughness={0.1}
          distort={0.3} 
          speed={2} 
        />
      </mesh>
    </Float>
  );
}

export default function Background3D() {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: -1, /* Keeps it behind your UI */
      pointerEvents: 'none' /* Ensures it doesn't block clicks */
    }}>
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1.5} />
        <Environment preset="city" />
        <AnimatedShape />
      </Canvas>
    </div>
  );
}