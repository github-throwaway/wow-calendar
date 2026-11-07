# Ludwigshafen WOW – Eventkalender als Abo

## Schnell: einmalig importieren
`ludwigshafen-wow.ics` öffnen bzw. in den Kalender importieren. Enthält alle aktuell
angekündigten Termine, aktualisiert sich aber nicht.

## Richtiges Abo (aktualisiert sich täglich, kostenlos über GitHub)
1. Auf github.com ein Konto anlegen und ein neues **öffentliches** Repository erstellen
   (z. B. `wow-kalender`).
2. `wow_kalender.py` und den Ordner `.github/workflows/kalender.yml` hochladen
   („Add file → Upload files“; den Pfad `.github/workflows/` beim Anlegen der Datei mit eintippen).
3. Reiter **Actions** → „WOW-Kalender aktualisieren“ → **Run workflow**. Danach liegt
   `ludwigshafen-wow.ics` im Repository und wird jeden Morgen neu gebaut.
4. Abo-Adresse:
   `https://raw.githubusercontent.com/github-throwaway/wow-calendar/main/ludwigshafen-wow.ics`
   - iPhone: Einstellungen → Kalender → Accounts → Account hinzufügen → Andere →
     Kalenderabo hinzufügen → Adresse einfügen.
   - Google Kalender (am Computer): „Weitere Kalender +“ → „Per URL“.
   - Outlook: Kalender hinzufügen → Aus dem Internet abonnieren.

Hinweis: Das Skript nutzt die öffentlichen Einzeltermin-Exporte der Website. Ändert
ludwigshafen-wow.de seinen Aufbau, muss das Skript evtl. angepasst werden.
