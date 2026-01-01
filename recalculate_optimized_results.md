# Optimize Edilmiş Sonuçları Tekrar Hesaplama

## 20 PR için Optimize Edilmiş Sonuçları Hesaplama

### PR ID'leri:
- **10 Django PR:** 20446, 20447, 20448, 20449, 20450, 20451, 20452, 20453, 20454, 20455
- **10 FastAPI PR:** 14584, 14585, 14586, 14587, 14588, 14589, 14591, 14592, 14593, 14594

### Komut:

```bash
poetry run python -m app.cli evaluate \
  --pr-ids "20446,20447,20448,20449,20450,20451,20452,20453,20454,20455,14584,14585,14586,14587,14588,14589,14591,14592,14593,14594" \
  --aggregate \
  --use-stored \
  --system multi_agent
```

### Açıklama:
- `--pr-ids`: Hesaplanacak PR ID'leri (virgülle ayrılmış)
- `--aggregate`: Sonuçları tek bir dosyada topla
- `--use-stored`: Mevcut review'ları kullan (yeniden review yapma)
- `--system multi_agent`: Multi-agent sistemi kullan

### Sonuç Dosyası:
`eval/results/evaluation_multi_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json`

### Not:
Review'lar `reviews/` klasöründe mevcut olmalı. Eğer review'lar yoksa, önce review yapılması gerekir.

