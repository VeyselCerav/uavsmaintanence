"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { notificationHref, notificationMeta } from "@/lib/notification";
import { useI18n } from "@/lib/i18n-context";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/services/notifications";

export default function NotificationsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["notifications", "all"],
    queryFn: () => listNotifications(false),
  });
  const items = query.data?.data ?? [];
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["notifications"] });
    await queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
  };
  const readOne = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: invalidate,
  });
  const readAll = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: invalidate,
  });
  const error = query.error instanceof Error ? query.error.message : null;

  return (
    <section>
      <PageHeader title={t("notifications.title")}>
        <Button type="button" variant="outline" onClick={() => readAll.mutate()}>
          {t("notifications.markAll")}
        </Button>
      </PageHeader>
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      <Card className="py-0">
        <CardContent className="p-0">
          {items.length === 0 ? (
            <p className="px-4 py-6 text-sm text-muted-foreground">{t("notifications.empty")}</p>
          ) : (
            <ul>
              {items.map((item) => (
                <li key={item.id} className="border-t px-4 py-3 text-sm first:border-t-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className={`font-medium ${item.is_read ? "text-secondary" : "text-primary"}`}>
                        {t(item.title_key)}
                      </p>
                      <p className="text-secondary">{t(item.body_key)}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{notificationMeta(item)}</p>
                      {notificationHref(item) ? (
                        <Button asChild variant="link" size="sm" className="mt-1 h-auto px-0 text-info">
                          <Link href={notificationHref(item) ?? "/notifications"}>
                            {item.payload.work_order_number ?? item.payload.uav_registration}
                          </Link>
                        </Button>
                      ) : null}
                    </div>
                    {item.is_read ? null : (
                      <Button
                        type="button"
                        variant="link"
                        size="sm"
                        className="h-auto px-0 text-info"
                        onClick={() => readOne.mutate(item.id)}
                      >
                        {t("notifications.markRead")}
                      </Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
