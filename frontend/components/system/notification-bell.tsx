"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { notificationHref, notificationMeta } from "@/lib/notification";
import { useI18n } from "@/lib/i18n-context";
import {
  getUnreadCount,
  listNotifications,
  markNotificationRead,
} from "@/services/notifications";

export function NotificationBell() {
  const { t } = useI18n();
  const router = useRouter();
  const queryClient = useQueryClient();
  const countQuery = useQuery({
    queryKey: ["notifications-unread"],
    queryFn: getUnreadCount,
    refetchInterval: 20000,
  });
  const listQuery = useQuery({
    queryKey: ["notifications", "preview"],
    queryFn: () => listNotifications(true),
  });
  const unread = countQuery.data?.unread ?? 0;
  const items = listQuery.data?.data ?? [];
  const readMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
      await queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button type="button" variant="ghost" size="icon" className="relative text-secondary" aria-label={t("notifications.title")}>
          <Bell />
          {unread > 0 ? (
            <span className="absolute -right-0.5 -top-0.5 min-w-4 rounded-full bg-danger px-1 text-center text-[10px] leading-4 text-white">
              {unread > 99 ? "99+" : unread}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 min-w-80">
        <DropdownMenuLabel className="flex items-center justify-between text-sm text-foreground">
          <span>{t("notifications.title")}</span>
          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
            <Link href="/notifications">{t("notifications.all")}</Link>
          </Button>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {items.length === 0 ? (
          <p className="px-2 py-4 text-sm text-muted-foreground">{t("notifications.empty")}</p>
        ) : (
          items.slice(0, 8).map((item) => (
            <DropdownMenuItem
              key={item.id}
              className="flex-col items-start gap-0.5"
              onSelect={() => {
                readMutation.mutate(item.id);
                const href = notificationHref(item);
                router.push(href ?? "/notifications");
              }}
            >
              <span className="font-medium text-primary">{t(item.title_key)}</span>
              <span className="text-xs text-secondary">{notificationMeta(item)}</span>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
