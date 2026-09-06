# Aktarım bekleyen değil — `seed_fleet` yükler

Kaynak dosya kopyası: `backend/apps/uavs/data/iha-katalog-acik-kaynak.json`

```powershell
docker compose exec backend python manage.py seed_fleet
# veya yeniden yüklemek için
docker compose exec backend python manage.py seed_fleet --force
```
