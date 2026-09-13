import type {
  AssetLayer,
  CaMethod,
  Control,
  DataClass,
  Flow,
  ProductSeed,
  Regime,
  Retrieval,
  SystemEntry,
} from "@/lib/types/authoring";

import productsJson from "./products.json";
import dataClassesJson from "./data-classes.json";
import regimesJson from "./regimes.json";
import systemsJson from "./systems.json";
import controlsJson from "./controls.json";
import layersJson from "./layers.json";
import flowsJson from "./flows.json";
import optionsJson from "./options.json";

export const PRODUCTS = productsJson as unknown as ProductSeed[];
export const DATA_CLASSES = dataClassesJson as unknown as DataClass[];
export const REGIMES = regimesJson as unknown as Regime[];
export const SYSTEMS = systemsJson as unknown as SystemEntry[];
export const CONTROLS = controlsJson as unknown as Control[];
export const LAYERS = layersJson as unknown as AssetLayer[];
export const FLOWS = flowsJson as unknown as Flow[];
export const ART_RET = optionsJson.ART_RET as Record<Retrieval, string>;
export const CA = optionsJson.CA as Record<CaMethod, string>;

/** Demo company profile — genericized. */
export const COMPANY = "Meridian Financial";
