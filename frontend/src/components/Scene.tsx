import { Html, OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { Component, Suspense, useEffect, useRef, type ReactNode } from "react";
import * as THREE from "three";

export interface PinData {
  id: string;
  name: string;
  position: [number, number, number];
}

interface OrbitLike {
  target: THREE.Vector3;
  update: () => void;
  addEventListener: (type: string, listener: () => void) => void;
  removeEventListener: (type: string, listener: () => void) => void;
}

function CameraFocus({ focusKey, focus }: { focusKey: string | null; focus: [number, number, number] | null }) {
  const { camera, controls } = useThree();
  const focusRef = useRef(focus);
  const anim = useRef<{ target: THREE.Vector3; cam: THREE.Vector3 } | null>(null);
  focusRef.current = focus;

  useEffect(() => {
    const orbit = controls as OrbitLike | null;
    const point = focusRef.current;
    if (!point || !orbit) return;
    const target = new THREE.Vector3(...point);
    const offset = camera.position.clone().sub(orbit.target);
    const distance = offset.length();
    const desired = distance > 6 || distance < 1.5 ? offset.setLength(4.2) : offset;
    anim.current = { target, cam: target.clone().add(desired) };
    const stop = () => {
      anim.current = null;
    };
    orbit.addEventListener("start", stop);
    return () => orbit.removeEventListener("start", stop);
  }, [focusKey, camera, controls]);

  useFrame(() => {
    const orbit = controls as OrbitLike | null;
    if (!anim.current || !orbit) return;
    orbit.target.lerp(anim.current.target, 0.12);
    camera.position.lerp(anim.current.cam, 0.12);
    orbit.update();
    if (orbit.target.distanceTo(anim.current.target) < 0.04) anim.current = null;
  });

  return null;
}

function Pin({ pin, selected, onSelect }: { pin: PinData; selected: boolean; onSelect: (id: string) => void }) {
  const select = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    onSelect(pin.id);
  };
  return (
    <group position={pin.position}>
      <mesh position={[0, 0.16, 0]} onClick={select} castShadow>
        <sphereGeometry args={[selected ? 0.12 : 0.09, 24, 24]} />
        <meshStandardMaterial
          color={selected ? "#d97706" : "#0f766e"}
          emissive={selected ? "#b45309" : "#115e59"}
          emissiveIntensity={0.45}
        />
      </mesh>
      <mesh position={[0, 0.05, 0]} onClick={select}>
        <cylinderGeometry args={[0.018, 0.018, 0.12, 12]} />
        <meshStandardMaterial color="#334155" />
      </mesh>
      {selected && (
        <Html position={[0, 0.38, 0]} center distanceFactor={8}>
          <div className="rounded-md bg-slate-900/90 px-2 py-1 text-xs whitespace-nowrap text-white shadow">{pin.name}</div>
        </Html>
      )}
    </group>
  );
}

function Floor({
  placing,
  onFloor,
}: {
  placing: boolean;
  onFloor: (point: { x: number; z: number }) => void;
}) {
  return (
    <mesh
      rotation={[-Math.PI / 2, 0, 0]}
      position={[0, 0, 0]}
      receiveShadow
      onClick={(event) => {
        event.stopPropagation();
        onFloor({ x: event.point.x, z: event.point.z });
      }}
    >
      <planeGeometry args={[10, 8]} />
      <meshStandardMaterial color={placing ? "#d6ebe6" : "#e7e5e4"} />
    </mesh>
  );
}

function ProceduralRoom({ placing, onFloor }: { placing: boolean; onFloor: (point: { x: number; z: number }) => void }) {
  return (
    <group>
      <Floor placing={placing} onFloor={onFloor} />
      <gridHelper args={[10, 10, "#cbd5e1", "#e2e8f0"]} position={[0, 0.01, 0]} raycast={() => null} />
      <mesh position={[0, 1.5, -4]} receiveShadow>
        <boxGeometry args={[10, 3, 0.08]} />
        <meshStandardMaterial color="#f8fafc" />
      </mesh>
      <mesh position={[-5, 1.5, 0]} receiveShadow>
        <boxGeometry args={[0.08, 3, 8]} />
        <meshStandardMaterial color="#f1f5f9" />
      </mesh>
      <mesh position={[5, 1.5, 0]} receiveShadow>
        <boxGeometry args={[0.08, 3, 8]} />
        <meshStandardMaterial color="#f1f5f9" />
      </mesh>
      <mesh position={[0, 0.45, -2.2]} castShadow receiveShadow>
        <boxGeometry args={[3.4, 0.9, 0.9]} />
        <meshStandardMaterial color="#cbd5e1" />
      </mesh>
      <mesh position={[-4.25, 0.825, 0.2]} castShadow>
        <boxGeometry args={[0.7, 0.05, 3.2]} />
        <meshStandardMaterial color="#94a3b8" />
      </mesh>
      <mesh position={[-4.25, 1.325, 0.2]} castShadow>
        <boxGeometry args={[0.7, 0.05, 3.2]} />
        <meshStandardMaterial color="#94a3b8" />
      </mesh>
      <mesh position={[-4.55, 0.8, 0.2]}>
        <boxGeometry args={[0.06, 1.6, 3.2]} />
        <meshStandardMaterial color="#64748b" />
      </mesh>
      <mesh position={[4.15, 0.8, -2.4]} castShadow>
        <boxGeometry args={[0.8, 1.6, 1.05]} />
        <meshStandardMaterial color="#94a3b8" />
      </mesh>
    </group>
  );
}

function GlbModel({ url }: { url: string }) {
  const gltf = useGLTF(url);
  return <primitive object={gltf.scene} />;
}

class ModelBoundary extends Component<{ children: ReactNode; onError: () => void }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch() {
    this.props.onError();
  }

  render() {
    if (this.state.failed) return null;
    return this.props.children;
  }
}

export function Scene({
  pins,
  selectedId,
  focusKey,
  focus,
  placing,
  draft,
  glbUrl,
  onSelect,
  onFloor,
  onGlbError,
}: {
  pins: PinData[];
  selectedId: string | null;
  focusKey: string | null;
  focus: [number, number, number] | null;
  placing: boolean;
  draft: { x: number; y: number; z: number } | null;
  glbUrl: string | null;
  onSelect: (id: string) => void;
  onFloor: (point: { x: number; z: number }) => void;
  onGlbError: () => void;
}) {
  return (
    <Canvas camera={{ position: [6.5, 5.2, 6.2], fov: 42 }} shadows>
      <color attach="background" args={["#dbe3ea"]} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[4, 8, 3]} intensity={1.15} castShadow />
      <Suspense fallback={null}>
        {glbUrl ? (
          <>
            <Floor placing={placing} onFloor={onFloor} />
            <ModelBoundary onError={onGlbError}>
              <GlbModel url={glbUrl} />
            </ModelBoundary>
          </>
        ) : (
          <ProceduralRoom placing={placing} onFloor={onFloor} />
        )}
      </Suspense>
      {pins.map((pin) => (
        <Pin key={pin.id} pin={pin} selected={pin.id === selectedId} onSelect={onSelect} />
      ))}
      {draft && (
        <mesh position={[draft.x, draft.y + 0.16, draft.z]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#0369a1" transparent opacity={0.85} />
        </mesh>
      )}
      <OrbitControls makeDefault maxPolarAngle={Math.PI / 2.05} minDistance={1.4} maxDistance={18} target={[0, 0.8, 0]} />
      <CameraFocus focusKey={focusKey} focus={focus} />
    </Canvas>
  );
}
