import { apiFetch } from "@/services/api";

export type SearchHit = {
  entity: string;
  id: string;
  title: string;
  subtitle: string;
  href: string;
};

export type SearchGroup = {
  entity: string;
  items: SearchHit[];
};

export function searchGlobal(query: string) {
  return apiFetch<{ query: string; groups: SearchGroup[] }>(
    `/search/?q=${encodeURIComponent(query)}`,
  );
}
