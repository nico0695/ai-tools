export type Scope = 'user' | 'project';
export type UnitKind = 'dir' | 'sync-dir';
export type ExistingMode = 'unmanaged' | 'update';

export interface Context {
  scope: Scope;
  base: string;
  repo: string;
  providers: string[];
  providerDir(id: string): string;
}

export interface Group { id: string; note?: string; default?: boolean; }
export interface Item { id: string; description: string; group?: string; }

export interface Unit {
  item: string;
  provider?: string;
  kind: UnitKind;
  src: string;
  dest: string;
  exclude?: string[];
  preserve?: string[];
}

export interface Installer {
  id: string;
  label: string;
  scopes: Scope[];
  providers: string[];
  groups?: Group[];
  allowEmptyProviders?: boolean;
  allowSelf?: boolean;
  allowUninstall?: boolean;
  existing?: ExistingMode;
  items(): Item[];
  units(item: Item, ctx: Context): Unit[];
  nextSteps?(ctx: Context): string[];
}
