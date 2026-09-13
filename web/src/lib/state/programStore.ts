"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  CaMethod,
  Control,
  ControlFn,
  Nature,
  ProductState,
  Retrieval,
  SystemEntry,
  Tri,
} from "@/lib/types/authoring";
import { CONTROLS, PRODUCTS, SYSTEMS } from "@/data/seed";

export interface ProgramState {
  products: Record<string, ProductState>;
  systems: SystemEntry[];
  controls: Control[];
  openDoms: Record<string, boolean>;
  selectedCp: string;
  /* products / scope */
  toggleProduct: (id: string) => void;
  toggleProductOpen: (id: string) => void;
  toggleClass: (pid: string, cid: string) => void;
  toggleLayer: (pid: string, li: number) => void;
  setAssetItem: (pid: string, li: number, ii: number, v: Tri) => void;
  resetScope: () => void;
  /* systems */
  setSystemScope: (id: string, v: Tri) => void;
  addSystem: (name: string) => void;
  /* controls */
  toggleDom: (dom: string) => void;
  setNature: (c: string, v: Nature) => void;
  setFn: (c: string, v: ControlFn) => void;
  toggleComp: (c: string) => void;
  toggleCtlSystem: (c: string, sysId: string) => void;
  /* datasets (write-through across every owning control) */
  setDatasetRet: (sys: string, art: string, v: Retrieval) => void;
  setDatasetCa: (sys: string, art: string, v: CaMethod) => void;
  /* process graph */
  selectCp: (id: string) => void;
}

const DOMS = [...new Set(CONTROLS.map((x) => x.dom))];

function seedProducts(): Record<string, ProductState> {
  const out: Record<string, ProductState> = {};
  PRODUCTS.forEach((p) => {
    out[p.id] = {
      on: p.on,
      open: false,
      cls: [...p.cls],
      items: {},
      layersOpen: {},
    };
  });
  return out;
}

function seedOpenDoms(): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  DOMS.forEach((d, i) => (out[d] = i < 2));
  return out;
}

function cloneControls(): Control[] {
  return CONTROLS.map((c) => ({
    ...c,
    sys: [...c.sys],
    ds: c.ds.map((d) => ({ ...d })),
  }));
}

export const useProgramStore = create<ProgramState>()(
  persist(
    (set) => ({
      products: seedProducts(),
      systems: SYSTEMS.map((s) => ({ ...s })),
      controls: cloneControls(),
      openDoms: seedOpenDoms(),
      selectedCp: "CM-1",

      toggleProduct: (id) =>
        set((st) => {
          const p = st.products[id];
          const on = !p.on;
          return {
            products: {
              ...st.products,
              [id]: { ...p, on, open: on ? true : p.open },
            },
          };
        }),

      toggleProductOpen: (id) =>
        set((st) => {
          const p = st.products[id];
          if (!p.on) {
            return { products: { ...st.products, [id]: { ...p, on: true, open: true } } };
          }
          return { products: { ...st.products, [id]: { ...p, open: !p.open } } };
        }),

      toggleClass: (pid, cid) =>
        set((st) => {
          const p = st.products[pid];
          const cls = p.cls.includes(cid)
            ? p.cls.filter((c) => c !== cid)
            : [...p.cls, cid];
          return { products: { ...st.products, [pid]: { ...p, cls } } };
        }),

      toggleLayer: (pid, li) =>
        set((st) => {
          const p = st.products[pid];
          return {
            products: {
              ...st.products,
              [pid]: {
                ...p,
                layersOpen: { ...p.layersOpen, [li]: !p.layersOpen[li] },
              },
            },
          };
        }),

      setAssetItem: (pid, li, ii, v) =>
        set((st) => {
          const p = st.products[pid];
          return {
            products: {
              ...st.products,
              [pid]: { ...p, items: { ...p.items, [`${li}:${ii}`]: v } },
            },
          };
        }),

      resetScope: () => set({ products: seedProducts() }),

      setSystemScope: (id, v) =>
        set((st) => ({
          systems: st.systems.map((s) => (s.id === id ? { ...s, v } : s)),
        })),

      addSystem: (name) =>
        set((st) => ({
          systems: [
            ...st.systems,
            { id: "x" + Date.now(), name, cat: "Third parties", v: "unk" },
          ],
        })),

      toggleDom: (dom) =>
        set((st) => ({ openDoms: { ...st.openDoms, [dom]: !st.openDoms[dom] } })),

      setNature: (c, v) =>
        set((st) => ({
          controls: st.controls.map((x) => (x.c === c ? { ...x, nat: v } : x)),
        })),

      setFn: (c, v) =>
        set((st) => ({
          controls: st.controls.map((x) => (x.c === c ? { ...x, fn: v } : x)),
        })),

      toggleComp: (c) =>
        set((st) => ({
          controls: st.controls.map((x) =>
            x.c === c ? { ...x, comp: !x.comp } : x
          ),
        })),

      toggleCtlSystem: (c, sysId) =>
        set((st) => ({
          controls: st.controls.map((x) => {
            if (x.c !== c) return x;
            const sys = x.sys.includes(sysId)
              ? x.sys.filter((s) => s !== sysId)
              : [...x.sys, sysId];
            return { ...x, sys };
          }),
        })),

      setDatasetRet: (sys, art, v) =>
        set((st) => ({
          controls: st.controls.map((x) => ({
            ...x,
            ds: x.ds.map((d) =>
              d.sys === sys && d.art === art ? { ...d, ret: v } : d
            ),
          })),
        })),

      setDatasetCa: (sys, art, v) =>
        set((st) => ({
          controls: st.controls.map((x) => ({
            ...x,
            ds: x.ds.map((d) =>
              d.sys === sys && d.art === art ? { ...d, ca: v } : d
            ),
          })),
        })),

      selectCp: (id) => set({ selectedCp: id }),
    }),
    {
      name: "aegis-program-v1",
      skipHydration: true,
      partialize: (st) => ({
        products: st.products,
        systems: st.systems,
        controls: st.controls,
        openDoms: st.openDoms,
        selectedCp: st.selectedCp,
      }),
    }
  )
);
