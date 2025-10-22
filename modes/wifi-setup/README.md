# WiFi Setup Mode

Automatische configuratie mode die actief wordt wanneer de LED matrix geen WiFi verbinding kan maken.

## Werking

Deze mode wordt automatisch geactiveerd wanneer:
- De Raspberry Pi opstart zonder WiFi verbinding
- Er geen bekende WiFi netwerken beschikbaar zijn

## Visuele feedback

De matrix toont een pulserend WiFi icoon in blauw/cyaan om aan te geven dat de configuratie portal actief is.

## Configureren

1. Zoek op je telefoon/laptop naar het WiFi netwerk **"led-matrix"**
2. Verbind met dit netwerk (wachtwoord: **ledmatrix2024**)
3. Je browser opent automatisch de configuratie pagina (captive portal)
4. Selecteer je WiFi netwerk en voer het wachtwoord in
5. De Pi verbindt met het netwerk en de normale mode wordt hervat

## Technische details

Deze mode gebruikt [balena WiFi Connect](https://github.com/balena-os/wifi-connect) voor de captive portal functionaliteit.
