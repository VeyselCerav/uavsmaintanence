"use client";

import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Input } from "@/components/ui/input";
import { useI18n } from "@/lib/i18n-context";
import { searchGlobal, type SearchGroup } from "@/services/search";

export function GlobalSearch() {
  const { t } = useI18n();
  const router = useRouter();
  const [term, setTerm] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handle = window.setTimeout(() => setDebounced(term.trim()), 250);
    return () => window.clearTimeout(handle);
  }, [term]);

  const query = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => searchGlobal(debounced),
    enabled: debounced.length >= 2,
  });
  const groups: SearchGroup[] = query.data?.groups ?? [];

  return (
    <div className="relative w-64">
      <Search className="pointer-events-none absolute top-2 left-2 size-4 text-muted-foreground" />
      <Input
        className="pl-8"
        value={term}
        placeholder={t("common.search")}
        onChange={(event) => {
          setTerm(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => window.setTimeout(() => setOpen(false), 150)}
      />
      {open && debounced.length >= 2 ? (
        <div className="absolute z-20 mt-1 max-h-80 w-[22rem] overflow-auto rounded-lg border bg-card p-2 shadow-lg">
          {query.isLoading ? (
            <p className="px-2 py-1 text-xs text-muted-foreground">{t("common.loading")}</p>
          ) : null}
          {!query.isLoading && groups.length === 0 ? (
            <p className="px-2 py-1 text-xs text-muted-foreground">{t("search.empty")}</p>
          ) : null}
          {groups.map((group) => (
            <div key={group.entity} className="mb-2 last:mb-0">
              <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {t(`search.entity.${group.entity}`)}
              </p>
              {group.items.map((item) => (
                <Link
                  key={`${item.entity}-${item.id}`}
                  href={item.href}
                  className="block rounded-md px-2 py-1.5 hover:bg-muted"
                  onMouseDown={(event) => {
                    event.preventDefault();
                    router.push(item.href);
                    setOpen(false);
                    setTerm("");
                  }}
                >
                  <p className="text-sm text-foreground">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.subtitle}</p>
                </Link>
              ))}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
