# Dokumentation: sentiment_enriched_complete.parquet

## Übersicht

Diese Parquet-Datei enthält alle Twitter-Sentiment-Daten auf Tweet-Ebene, erweitert um stündliche Bitcoin-Preisdaten und aggregierte Sentiment-Metriken. Jede Zeile repräsentiert einen einzelnen Tweet mit dem Kontext der Bitcoin-Marktbedingungen zum Zeitpunkt seiner Veröffentlichung.[^1][^2]

## Datenstruktur

**Format:** Apache Parquet (komprimiert, spaltenorientiert)[^5][^6]
**Granularität:** Tweet-Ebene (ein Tweet pro Zeile)
**Anzahl Tweets:** ~15,6 Millionen
**Zeitraum:** 2021-01-01 bis 2021-12-31
**Index:** Numerischer Index (reset nach Merge)

***

## Spalten-Dokumentation

### Tweet-Daten (Original)

| Spalte | Datentyp | Beschreibung |
| :-- | :-- | :-- |
| `datetime` | datetime64[ns] | Zeitstempel der Tweet-Veröffentlichung (sekundengenau, UTC) |
| `sentiment` | object | Klassifizierte Sentiment-Kategorie: 'positive', 'negative', 'neutral' |
| `sentiment_score` | float64 | Numerischer Sentiment-Score des Tweets. Wertebereich: -1.0 (sehr negativ) bis +1.0 (sehr positiv) |

**Zusätzliche Tweet-Felder** (falls vorhanden): `text`, `user_id`, `tweet_id`, etc.

***

### Bitcoin Preisdaten (Stündlich)

| Spalte | Datentyp | Beschreibung |
| :-- | :-- | :-- |
| `open` | float64 | Bitcoin-Eröffnungspreis (USD) zu Beginn der Stunde, in der der Tweet veröffentlicht wurde |
| `high` | float64 | Höchster Bitcoin-Preis (USD) während der Stunde |
| `low` | float64 | Niedrigster Bitcoin-Preis (USD) während der Stunde |
| `close` | float64 | Bitcoin-Schlusspreis (USD) am Ende der Stunde |
| `volume` | float64 | Gesamtes Handelsvolumen (USD) während der Stunde |

**Quelle:** Minutengenaue BTC-Daten, aggregiert zu OHLC-Stundenwerten

***

### Aggregierte Sentiment-Metriken (Stündlich)

| Spalte | Datentyp | Beschreibung |
| :-- | :-- | :-- |
| `avg_score` | float64 | Durchschnittlicher Sentiment-Score aller Tweets in derselben Stunde (-1.0 bis +1.0) |
| `sentiment_median` | float64 | Median des Sentiment-Scores der Stunde. Robuster gegen Ausreißer |
| `n_positive` | int64 | Anzahl positiver Tweets in derselben Stunde |
| `n_negative` | int64 | Anzahl negativer Tweets in derselben Stunde |
| `total_tweets` | int64 | Gesamtanzahl aller Tweets in derselben Stunde |
| `sentiment_mode` | object | Häufigste Sentiment-Kategorie der Stunde ('positive', 'negative', 'neutral') |
| `net_sentiment` | int64 | Netto-Sentiment: `n_positive - n_negative`. Zeigt Übergewicht positiver/negativer Stimmung |


***

## Datenqualität \& Besonderheiten

### NaN-Werte

- **Tweets mit NaN bei BTC-Spalten:** Tweets außerhalb des Zeitraums der verfügbaren BTC-Daten
- **Empfehlung:** Verwende `sentiment_enriched_complete_clean.parquet` für Analysen (nur Tweets mit vollständigen Daten)


### Merge-Logik

- Tweets werden ihrer **stündlichen** Zeitgruppe zugeordnet (`datetime.floor('h')`)
- **Left Join:** Alle Tweets bleiben erhalten, auch ohne BTC-Match[^8]
- BTC-Daten wiederholen sich für alle Tweets innerhalb derselben Stunde

***




