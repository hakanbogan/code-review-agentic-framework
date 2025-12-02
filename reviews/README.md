# Review Storage

Bu dizin tüm code review sonuçlarını organize eder.

## Yapı

```
reviews/
├── index.json              # Tüm review'ların özet index'i
├── {pr_id}/
│   ├── review.md          # Markdown formatında review comment
│   └── review.json        # Tam review sonucu (JSON)
```

## Kullanım

### Review'ları Listele

```bash
poetry run python -m app.cli list-reviews
poetry run python -m app.cli list-reviews --limit 20
```

### Belirli Bir Review'ı Göster

```bash
poetry run python -m app.cli show-review 13977
```

### Yeni Review Yap

Review yapıldığında otomatik olarak bu dizine kaydedilir:

```bash
poetry run python -m app.cli review /path/to/repo \
  --pr-id "123" \
  --title "PR Title" \
  --description "Description" \
  --language python
```

### GitHub PR'larını Review Et

```bash
poetry run python scripts/review_github_prs.py owner repo --limit 5
```

## Index Formatı

`index.json` dosyası tüm review'ların özet bilgilerini içerir:

```json
{
  "13977": {
    "pr_id": "13977",
    "title": "Add bubble_sort_optimized",
    "repository": "TheAlgorithms/Python",
    "system_type": "multi_agent",
    "findings_count": 6,
    "findings_by_severity": {
      "critical": 0,
      "major": 0,
      "minor": 6,
      "nit": 0
    },
    "review_time_s": 36.72,
    "token_cost": 0.0,
    "created_at": "2025-11-30T...",
    "reviewed_at": "2025-11-30T..."
  }
}
```

## Özellikler

- ✅ Otomatik organizasyon (her PR için ayrı klasör)
- ✅ Index sistemi (hızlı arama ve listeleme)
- ✅ Hem markdown hem JSON formatında saklama
- ✅ Özet istatistikler
- ✅ CLI komutları ile kolay erişim

