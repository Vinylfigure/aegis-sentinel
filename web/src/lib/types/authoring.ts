/* Authoring-domain types for the Aegis workbench (ported from the prototypes'
 * JS data arrays; see docs/prototypes/). */

export type Tri = "in" | "unk" | "out";
export type Nature = "cfg" | "auto" | "manual";
export type ControlFn = "prev" | "det";
export type Retrieval = "api" | "shot" | "log" | "man";
export type CaMethod = "recon" | "hash" | "trace" | "agent";

export interface DataClass {
  id: string;
  name: string;
  note: string;
  tier: string;
}

export interface ProductSeed {
  id: string;
  name: string;
  desc: string;
  cls: string[];
  on: boolean;
}

export interface Regime {
  id: string;
  name: string;
  why: string;
  on: string[]; // data-class ids that light this regime
}

export interface SystemEntry {
  id: string;
  name: string;
  cat: string;
  v: Tri;
}

export interface DatasetRef {
  sys: string; // system id
  art: string; // artifact name
  ret: Retrieval;
  ca: CaMethod;
}

export interface Control {
  c: string; // control code, e.g. AM-01
  n: string; // name
  dom: string; // domain
  d: string; // description
  nat: Nature;
  fn: ControlFn;
  comp: boolean;
  sys: string[]; // mapped system ids
  ds: DatasetRef[];
}

export interface AssetLayerItem {
  name: string;
  note: string;
}

export interface AssetLayer {
  n: string;
  items: AssetLayerItem[];
}

/* ---- process graph (FLOWS) ---- */

export interface FlowNode {
  key: string;
  label: string;
  sub: string;
  tier: number; // 1..3
}

export interface ControlPoint {
  id: string;
  name: string;
  nat: Nature;
  fn: ControlFn;
  what: string;
  el: string;
  api: string;
  ev: string;
  ca: string;
  gap: string;
}

export interface FlowStep {
  node?: FlowNode;
  cp?: ControlPoint;
}

export interface Flow {
  id: string;
  name: string;
  sub: string;
  seq: FlowStep[];
}

/* ---- store slices ---- */

export interface ProductState {
  on: boolean;
  open: boolean;
  cls: string[];
  items: Record<string, Tri>; // "layerIdx:itemIdx" -> tri (default unk)
  layersOpen: Record<string, boolean>;
}

/* ---- derived shapes ---- */

export interface DatasetEntry {
  sys: string;
  art: string;
  ret: Retrieval;
  ca: CaMethod;
  ctls: string[];
}

export interface CollectorMission {
  id: string; // C-01 …
  art: string;
  sysId: string;
  sysName: string;
  scopeUnresolved: boolean;
  surface: string;
  ca: string;
  cadence: string;
  ctls: string[];
}

export interface LlmTask {
  id: string; // A-01 …
  name: string;
  boundary: string;
  task: string; // manifest slug
}
