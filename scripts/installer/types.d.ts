export type Scope = 'user' | 'project';

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
  kind: 'dir';
  src: string;
  dest: string;
  exclude?: string[];
}

export interface Installer {
  id: string;
  label: string;
  scopes: Scope[];
  providers: string[];
  groups?: Group[];
  items(): Item[];
  units(item: Item, ctx: Context): Unit[];
}
