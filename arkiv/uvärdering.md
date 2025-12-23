Utvärdering av Copy/Paste – Editorial AI Control
Room
Introduktion
Med över 20 års erfarenhet som journalist närmar jag mig Copy/Paste – Editorial AI Control Room
med en kritisk blick. Det handlar om att bedöma om detta interna AI-verktyg verkligen matchar hur vi
journalister arbetar idag, och framför allt om det sparar tid utan att tumma på trovärdigheten. I denna
utvärdering går jag rakt på sak – inga överdrifter, bara en ärlig genomgång av nyttan och
begränsningarna. Bedömningen utgår från verktygsbeskrivningen, den medföljande jobbprofilen samt
aktuell branschfakta om journalistiskt arbete.
Dagens journalistiska arbetsflöde och utmaningar
En modern nyhetsreporter drunknar lätt i informationsflödet. Varje dag behöver vi:
Bevaka många källor: Pressmeddelanden, RSS-flöden, nyhetsbyråer, sociala medier och tips
från allmänheten. Allt ska skummas och sorteras under tidspress. Det manuella arbetet att
kontinuerligt övervaka och sortera nyhetskällor är tidskrävande, samtidigt som inget viktigt
får missas.
Verifiera och bearbeta information: Rykten och utkast måste dubbelkollas. Fakta ska bekräftas
i primärkällor, citat kontrolleras, och bakgrund tas fram. I praktiken har journalister ofta för lite
tid för noggrann faktagranskning. En studie indikerar t.ex. att vissa reportrar i snitt bara lägger
elva minuter om dagen på faktakoll – en siffra som speglar hur pressat schemat är .
Samtidigt är verifiering absolut nödvändigt för trovärdigheten.
Hantera tråkiga rutingöromål: Många arbetsmoment är repetitiva eller administrativa.
Exempelvis att transkribera intervjuer, översätta stycken text, eller sammanfatta långa dokument
för redaktionsmöten. Dessa uppgifter måste göras men stjäl värdefull tid från granskning och
kreativt arbete.
Konsekvensen av detta höga tempo är att vi journalister ibland ser AI inte som en lyx, utan som ett
potentiellt överlevnadsverktyg. Används AI rätt kan det accelerera monotona uppgifter och frigöra tid
– utan att ersätta det hantverk och omdöme som ligger till grund för trovärdig journalistik . Branschens
konsensus är att AI ska assistera, inte ersätta journalisten, samt att output från AI alltid måste
behandlas som ledtrådar, inte automatiska fakta . Med andra ord: vi kan låta maskinerna göra
grovjobbet, men den mänskliga faktakollen och berättarrösten förblir avgörande.
Vad är Copy/Paste och hur fungerar det?
Copy/Paste positionerar sig som ett produktionsnära AI-kontrollrum snarare än ännu en fristående app.
Det vill säga att AI-funktionerna byggts in i ett arbetsflöde som redaktionen själva kontrollerar.
Huvudkomponenterna och principerna är:
Linjär, spårbar AI-pipeline: All behandling av en nyhetssignal sker steg för steg och loggas.
Från input till utkast går informationen genom ett förutsägbart flöde som kan granskas i
•
•
1
•
2
3
•
1
efterhand. Inget mystiskt "black box"-chattande alltså, utan en tydlig kedja: Nyhetssignal →
Ingestering → Privacy Shield → AI-bearbetning → Utkast. Inga genvägar eller dolda sidospår. Detta
möjliggör att redaktionen exakt kan följa vad AI:n gjort med materialet och varifrån varje uppgift
kommer. En transparent AI-process med mänsklig överblick är helt avgörande för att behålla
förtroendet .
”Scout” – automatisk nyhetsbevakning: Copy/Paste inkluderar en komponent kallad Scout som
ständigt övervakar definierade RSS-flöden (exempelvis polisens nyhetssida, TT,
myndighetsbloggar). Scout deduplicerar och poängsätter nya händelser med en enkel
automatisk analys lokalt. Viktigt är att Scout inte hämtar fullständigt innehåll eller skickar
något externt; den skickar bara vidare en länk eller kort fallback-text som ett internt event. Det
innebär att systemet ger en strid ström av nyhetssignaler i realtid i kontrollrummets gränssnitt,
utan att riskera källskydd (mer om det nedan). Journalister kan direkt se vilka nya saker som
trillar in, och Scout kan även skicka notifieringar (t.ex. i Microsoft Teams) om något får högt
nyhetsvärde. I praktiken fungerar det som en ständig nyhetsradar som kan ersätta en del av
det manuella RSS-skummandet. Redaktionen får hjälp att snabbare identifiera vad som bör
prioriteras.
Manuella och automatiska inputs: Förutom automatik via Scout kan användaren även mata in
eget material: klistra in text (mejl, tips, egna anteckningar), ladda upp ett PDF-dokument, eller
ange en URL till en artikel. Allt sådant normaliseras till ett gemensamt ”Event”-format i systemet –
en slags standardiserad behållare för innehållet, oavsett källa. Det gör att resten av pipeline kan
behandla all inkommande info likadant. Denna enhetliga hantering minskar strul med format
och ser till att inget tappas bort i konverteringen.
Privacy Shield – inbyggt källskydd och GDPR-hantering: Innan någon extern AI-modell
involveras sker en lokal integritetsbehandling. Copy/Paste har ett ”Privacy Shield”-steg där alla
personuppgifter och känsliga data identifieras och anonymiseras internt. Namn ersätts t.ex.
med generiska taggar som [PERSON_A] , adresser och telefonnummer maskas, etc. Detta görs
helt lokalt, i minnet, med hjälp av en egen AI-modell eller regler – alltså ingen rådata med
identiteter lämnar någonsin det interna systemet. Först när texten är sanerad från PUL/PII går den
vidare till nästa steg. Denna design följer principerna om dataminimering och inbyggd säkerhet,
vilket inte bara är teoretiskt – det efterlevs tekniskt. För en journalist är detta enormt viktigt. Vi
har lagstadgat källskydd och GDPR att ta hänsyn till, och det är direkt olämpligt (t.o.m. farligt)
att mata in osekretessbelagda personuppgifter i öppna AI-tjänster online . Många
mediehus har förbjudit reportrar att klistra in opublicerat material i verktyg som ChatGPT på
grund av dessa risker. Copy/Paste löser den konflikten genom att bygga in ett robust skydd:
ingen känslig information lämnar huset. Resultatet är att journalister faktiskt kan dra nytta av
AI på riktigt material (t.ex. ett läckt dokument eller en råintervju) utan att riskera att bryta mot
källskyddet eller dataskyddslagar. Detta är ett praktexempel på att ta GDPR på allvar istället för att
ignorera det i ivern över AI.
AI-bearbetning med källhänvisningar: Efter anonymisering sker själva AI-bearbetningen. Här
används generativ AI (språkmodell) för att sammanfatta, strukturera och formulera ett
utkast på journalistisk text baserat på input-materialet. Den unika twisten är att Copy/Paste:s
AI inte får hitta på eller “gissa” fakta – varje påstående i utkastet kopplas maskinellt tillbaka till
underlaget. Systemet infogar tydliga markörer i texten som hänvisar till var i källmaterialet
uppgiften kommer ifrån. Det kan liknas vid fotnotsreferenser eller länkar: klickar man på en
markör hoppar man direkt till det ursprungliga stycket i källan som stödjer påståendet. Om AI:n
stöter på luckor eller något den inte kan styrka, så ska den flagga det i utkastet som en varning.
Denna metod, ofta kallad ”source-bound generation” eller RAG (Retrieval Augmented Generation),
4
•
•
•
5 6
•
2
syftar till att eliminera risken för fabricerade fakta. Som journalist har man ju nolltolerans mot
påhitt, så att verktyget tvingar fram transparens i varje rad är avgörande. Det ska inte gå att
smyga in en falsk uppgift – något som tyvärr hänt när slarviga reportrar använt AI okritiskt. (Ett
aktuellt exempel är reportern i USA som fick avgå efter att AI genererat citat som de citerade
personerna aldrig sagt . Sådana skandaler understryker varför spårbarhet är ett måste, inte
ett önskemål.)
Resultatet – verifierbart utkast: Det journalistiska utkast man får ut liknar till stilen en färdig
nyhetstext, men är tänkt som en början, inte en färdig produkt. Varje fakta har sin källa direkt
angiven i texten. Redaktören kan på ett ögonkast se vad som baseras på underlaget. Om någon
mening saknar källa innebär det att AI:n dragit en slutsats som inte direkt stöds – en tydlig
varningsklocka. Tanken är att reportern nu snabbt kan gå in och justera, förtydliga och
slutgiltigt kvalitetssäkra texten innan eventuell publicering. Copy/Paste publicerar inte åt
dig, utan liknar mer en mycket flitig researchassistent som levererar ett utkast komplett med
referenser. Den mänskliga journalisten är fortfarande den som fattar beslut, vinklar storyn och
skriver rubrikerna. Det här ligger helt i linje med branschens etik: AI är ett verktyg som hjälper
oss att göra journalistik, men gör inte jobbet åt oss . Målet är att spara tid och förbättra
kvaliteten, inte att automatisera bort redaktörens roll.
Gränssnitt och arbetssätt: Copy/Paste används via ett internt webbgränssnitt med två
huvudlägen. Pipeline-vy är där man hanterar ett enskilt nyhetsevent: man ser input-data, kan
manuellt trigga anonymisering och AI-generering och sedan granska utkastet i detalj. Consolevy
är kontrollrummet där alla inkommande signaler syns i lista (med färgmarkeringar eller poäng
från Scout). Där kan man prioritera, välja vilka som ska bearbetas, konfigurera bevakningar och
integrationer. Allt i samma verktyg – man slipper hoppa mellan separata applikationer för
nyhetsflöde, AI-sammanfattning, källkoll etc. En bonus är att systemet kan skicka ut pushnotiser
till t.ex. newsroom chat (Teams/Slack) för att uppmärksamma när något viktigt dyker upp, vilket
gör det proaktivt. I praktiken skulle en morgon på redaktionen kunna börja med att journalisten
öppnar Copy/Paste Console, får en snabb överblick över nattens händelser via Scout, och med
ett klick genererar utkast för de intressanta storyerna. Allt utan att klippa/klistra mellan en
massa separata verktyg.
Inte ett publiceringssystem: Det är värt att understryka vad Copy/Paste inte är. Det ersätter
inte CMS eller redigeringsprogram. Det publicerar inget direkt på sajt eller i print. Det är inte
heller en allmän “skrivassistans”-bot som man småpratar med. Det är ett specialbyggt internt
produktionsverktyg integrerat i dataflöden och arbetsprocesser. Fördelen med det är
fokusering: det är designat av journalister, för journalistik. Nackdelen är förstås att det inte går att
plocka upp från butikshyllan – det är en skräddarsydd lösning som Stampen Media utvecklar
själva och hostar själva, med allt vad det innebär av internt ansvar.
Sammanfattningsvis erbjuder Copy/Paste en helhetslösning för nyhetsinhämtning och AI-assisterad
textproduktion där varje steg är transparent och kontrollerbart. Tekniken bakom kulisserna
(maskininlärning, generativa modeller, RAG etc) må vara komplex, men för användaren presenteras det
som ett prydligt och logiskt arbetsflöde. Det liknar mer ett kontrollrum än en magisk låda. För en erfaren
journalist är detta i sig tilltalande – vi vill kunna granska processen, inte bara få ett mystiskt svar.
Systemet har byggts för att möta konkreta krav i en modern redaktion: snabbhet, källskydd,
noggrannhet och spårbarhet.
7
•
8
•
•
3
Sparad tid och ökad effektivitet
Kärnfrågan är om Copy/Paste faktiskt sparar tid för reportrarna, och om den tidsvinsten är värdefull.
Utifrån beskrivningen och vad vi vet om liknande AI-initiativ i branschen är svaret ja, på flera konkreta
sätt:
Automatisk nyhetsbevakning frigör tid: Att Scout ständigt sköter bevakningen av olika flöden
betyder att journalister slipper manuellt kontrollera varje enskild källa lika ofta. Istället för att
en reporter ska klicka runt på polisens pressrum, kommunens anslagstavla, TT-listor, Twitter mm
för att se om något nytt hänt, så centraliseras detta. Systemet kan omedelbart flagga nya
händelser. Det betyder att mindre tid går åt till att leta nyheter, mer tid kan läggas på att bedöma
och följa upp dem. Särskilt i lokala nyhetsmiljöer (Stampen har många lokaltidningar) är det guld
värt med en tidig heads-up på t.ex. en stor räddningsinsats eller ett viktigt pressmeddelande.
Tidsvinsten här är svår att kvantifiera, men tänk dig att Scout sparar 5–10 min varje timme i
minskat scrollande; över en arbetsdag och flera reportrar blir det många timmar som kan läggas
på innehållet istället för övervakningen.
Snabbare research och bakgrund: Genom att kunna mata in dokument och länkar och få ut ett
strukturerat sammandrag med källhänvisningar, kortas den inledande researchfasen drastiskt.
Ett konkret exempel: om en rapport på 80 sidor dimper ner, kan reportern låta Copy/Paste
generera en sammanfattning med nyckelinsikter. I stället för att spendera flera timmar på att
läsa och stryka under, får man kanske på några minuter en översikt av de viktigaste punkterna
med hänvisning till var i rapporten de står. Sedan kan man direkt klicka sig in på rätt ställe i
original-PDF:en för detaljer . Journalister i en studie har pekat ut just sammanfattning av
information som ett område där AI kan spara mycket tid . Copy/Paste kapitaliserar på det –
snabba sammanfattningar av t.ex. domstolsbeslut eller forskningsrön är ett utmärkt stöd för
att orientera sig . Givetvis måste man dubbelkolla kritiska uppgifter mot originalet, men
initialt har man sparat tid och fått vägledning om var man ska lägga sitt mänskliga fokus.
Utkast på artiklar utan blankt papper-syndrom: En av de mest tidsödande momenten kan
vara att skriva första utkastet på en artikel, särskilt när underlaget är omfattande eller rörigt.
Copy/Paste levererar ett färdigformulerat utkast med logisk struktur. Det kan jämföras med att
ha en junior kollega som gjort ett första skrivjobb åt dig, komplett med fotnoter var all info kom
ifrån. Detta kan spara betydande tid vid nyhetsskrivande. Journalisten kan gå direkt in i rollen
som granskare och redaktör av texten: stryka onödigt, lägga till ny info, justera tonalitet och
säkerställa att allt stämmer, istället för att börja från noll. Tidsbesparingen här kommer av att
skrivfasen går snabbare och att faktakällorna redan är uppspårade. Redaktören slipper ägna
minuter åt att leta upp den siffra eller citat som skulle in i texten – Copy/Paste har redan placerat
dem, med källhänvisning, i utkastet. Som exempel på effekt: Express.de i Tyskland har integrerat
en AI-assistent “Klara” som drar ut fakta och strukturerar sportreferat, vilket lett till markant
snabbare färdigställande av rutinartiklar . Skillnaden är att Copy/Paste inte publicerar 11% av
artiklarna på egen hand som Klara gör, men konceptet att en del av brödtexten kan genereras
automatiskt medför i praktiken att reportrarnas totala produktivitet ökar . De repetitiva
texterna tar mindre tid, vilket frigör tid för de svåra uppslagen.
Hantering av flera källor parallellt: En journalist måste ofta sammanfoga information från
flera ställen – kanske en polisrapport, en intervju och en tidigare artikel. Det innebär att jonglera
mellan fönster, kopiera citat, försäkra sig om att inget glöms. Copy/Paste kan ta in flera input
(flera länkar, textsnuttar) i samma event och generera en sammanhängande story som redan
kombinerar dessa bitar, med referenser. Det sparar hjärnkapacitet och tid: AI:n har redan gjort
•
•
9
10
11
•
12
13
•
4
ett utkast till hur pusselbitarna kan sitta ihop. Istället för att manuellt klippa in stycken från olika
källor och kanske missa något, har man ett utgångsdokument att förbättra. Återigen, det är
minuter här och där som snabbt blir timmar över en vecka.
Snabbare repetitiva uppgifter: Utöver textgenerering finns potential att Copy/Paste (eller dess
ekosystem) även skulle kunna integrera AI för transkribering av intervjuer eller översättning
av text. Verktygsbeskrivningen nämner inte uttryckligen talsignal input, men givet teamets
inriktning på dataflöden vore det logiskt att framtida versioner kan ta en ljudfil och använda en
lokal transkriptions-AI. Att få en intervju på 30 minuter omvandlad till text på säg 5 minuter
innebär en stor tidsbesparing jämfört med att manuellt skriva ut eller lyssna om flera gånger.
Journalister identifierar rutinmoment som transkribering och översättning som tacksamma att
låta AI hantera . Om Copy/Paste adresserar även de momenten blir det ett ännu mer
heltäckande tidsspararpaket.
Summerat tidsvärde: Alla ovan punkter handlar om att ta bort onödig latens i arbetsflödet. Om AI:n kan
ge oss en genväg för 30% av det mekaniska arbetet, så är det tid vi istället kan lägga på kvalitativa
delar: ringa det där extra samtalet, finputsa rubriken, gräva djupare i statistik. Flera
nyhetsorganisationer har redan visat att AI kan höja effektiviteten och ändå behålla kvalitet, just
genom att frigöra reportrarna för mer meningsfullt arbete . Associated Press till exempel har i över
ett decennium auto-genererat artiklar om bolagsrapporter och sportresultat, vilket gör att reportrarna
kan fokusera på uppföljning och analys istället. Samma princip gäller här: Copy/Paste kan ge
redaktionen mer tid att ägna åt kvalificerad journalistik, samtidigt som ingen tid spills på att jaga
fakta som redan finns. Som Agnes Stenbom (AI-forskare på KTH och Schibsted) uttrycker det: AI kan öka
effektiviteten i repetitiva processer och därmed frigöra tid för mer utforskande journalistiskt arbete . I ett
läge där redaktioner är slimmade och kraven höga, är det precis den vinsten man vill åt.
Transparens, tillit och källhänvisningar
Tillit är journalistikens valuta. Om publiken eller vi själva börjar tvivla på det vi skriver, raseras värdet.
Därför är transparens i AI-genererat innehåll helt nödvändig – något Copy/Paste verkar ha som
ledstjärna.
Genom att varje påstående i utkasten är kopplat till en källa adresseras en av de största orosmolnen
med AI: risken för hallucinationer eller felaktigheter som smyger sig in obemärkt. Istället får vi en
situation där varje faktabit är omedelbart verifierbar. Som reporter kan jag klicka på referensen och
se originalkontexten. Om något ser skumt ut, stryker eller ändrar jag det. Detta arbetssätt linjerar med
de rekommendationer som börjar växa fram i branschen: använd gärna AI för att samla info, men
”klicka alltid igenom till underliggande källa – AI-sammanfattningar kan vara ofullständiga eller
fel” . Copy/Paste underlättar just detta beteende, genom att servera källänkarna på silverfat.
Ur ett förtroendeperspektiv internt på redaktionen betyder spårbarheten också att AI:n blir enklare
att lita på. Transparensen är ett motgift mot den “magiska svartlåda”-misstro som många journalister
(med rätta) haft mot AI. När man ser var allt kommer ifrån minskar rädslan att AI:n hittar på. Projekt
Spinoza – ett liknande AI-verktyg framtaget med franska journalister – noterade att just det faktum att
verktygets databaser och logik byggts upp av journalistkollegor ökade användarnas förtroende:
"Spinozas databaser är uppbyggda av journalister, vilket gör att vi är mer benägna att lita på verktyget" .
Copy/Paste har en liknande aura då det är ett inhouse-verktyg format efter journalistiska principer, inte
en generisk kommersiell AI-tjänst. All kod och data bor inom det egna mediehuset, vilket inger ett
internt lugn – man vet att inga konstigheter sker i det fördolda.
•
14 15
5
16
17
18
5
För publiken i nästa led kan transparensen också kommuniceras. Även om själva Copy/Paste-utkasten
inte är tänkta att publiceras rått (de ska ju arbetas om av reportern), så kan man tänka sig att vissa
källhänvisningar följer med till slutprodukten. Några mediehus har börjat skylta med när AI varit
involverad i framställningen av en text, men det är en balansgång eftersom läsarundersökningar visat
att förtroendet kan dippa om något är AI-genererat . En kompromiss är att vara transparent
internt och i metodartiklar, men i själva nyhetstexten nöja sig med vanliga källcitat och attribut. Copy/
Paste kan hjälpa här genom att se till att reportern verkligen har koll på källorna – och kan plocka in
dem som vanliga referenser i brödtexten. Ingenting i utkastet baseras på "förmodat allmänt vetande"
eller AI-gissningar; allt vilar på identifierade källor, annars flaggas det. En sådan källa-för-källa
noggrannhet ligger nära hur faktagranskare på större redaktioner jobbar manuellt (ibland går de
igenom varje mening i ett reportage och kräver belägg för den). Här får reportern det arbetet delvis
förberett, vilket både sparar tid och höjer kvaliteten. Vi minskar risken att felaktiga uppgifter slinker
igenom oexaminerade.
Tillitsfrågan gäller också själva arbetsprocessen: att chefer och allmänhet kan lita på att journalistiken
inte urvattnas av AI. En uttalad oro är att om AI genererar mycket innehåll kan det leda till
slentrianmässig rapportering eller plagierad stil. Agnes Stenbom påpekade risken att om AI ”enbart
används för att öka, och inte förändra, medieproduktionen” kan kvaliteten försämras – texterna blir
likriktade och förlorar kreativitet . Copy/Paste försöker undvika den fällan genom att lägga
kontrollen hos journalisten i varje steg. Verktyget spottar inte ur sig färdiga artiklar på egen hand i
stora mängder; det måste finnas en människa som granskar och trycker igenom varje utkast. Det
fungerar mer som en smart förlängning av journalistens egna händer, inte som en automatröst. Detta
innebär att originalitet och vinklar fortfarande är något redaktionen formar aktivt. AI-utkasten är
underlag, inte färdig storytelling. Alltså behåller man det journalistiska hantverket och omdömet, men
får ett kraftfullt hjälpmedel för research och text.
Ett konkret exempel på hur transparens och mänsklig kontroll lönar sig är Associated Press policy: de
använder sedan länge AI för t.ex. ekonomi- och sportnotiser, men de flesta AP-journalister får inte
använda generativ AI för publicerat material utan mänsklig granskning . När de använder det (t.ex.
automatöversättning) lägger de till en not om att teknik användes, för att vara ärliga mot läsarna .
Detta visar att man kan integrera AI, spara tid, men ändå hålla transparensen högt. Copy/Paste är byggt
i samma anda – att öppenhet och ansvarighet är förval, inte något man löser i efterhand. Varje
redaktionsmedlem kan se vad AI:n gjort, och om en chef undrar “Hur tog vi fram det här?”, så finns hela
spårningen. Skulle något fel ändå slinka med kan man i efterhand göra en “root cause analysis” via
loggen, istället för att stå handfallen.
Sammanfattningsvis stärker Copy/Paste förutsättningarna för att AI används på ett pålitligt och
etiskt sätt. Det hjälper journalisten hålla sig till verifierade fakta och behålla kontrollen, vilket i sin tur
bygger förtroende både internt och externt. Som en journalist som testade Spinoza sa: “det är
redaktionellt drivet och inte gör jobbet åt oss – det hjälper oss att göra journalistik” . Precis så framstår
Copy/Paste också vilja fungera. Tillit kommer från transparens och ansvarstagande, och verktyget
möjliggör båda dessa i en AI-kontext.
Datasäkerhet och integritet
I en tid då mediehusen är mål för cyberattacker och data läckor, kan inte datasäkerhet överskattas.
Journalister har dessutom en skyldighet att hantera källmaterial varsamt – det kan röra sig om
dokument som avslöjar någons identitet eller känsliga uppgifter som inte får spridas. Copy/Paste har
integritet inbyggt i arkitekturen och det är en av dess stora styrkor jämfört med många generella AItjänster.
19
20
5
21
8
6
Som nämnt sker anonymisering av personuppgifter innan AI-bearbetning. Det innebär att även om
man använder en stor språkmodell i molnet (t.ex. OpenAI eller liknande) via Copy/Paste, så kommer
inga namn eller identifierande detaljer lämna organisationens servrar i klartext. AI:n jobbar på en
pseudonymiserad text. Det här är kritiskt ur GDPR-synpunkt. GDPR kräver bl.a. purpose limitation och
data minimization – att man bara hanterar persondata när det är nödvändigt och med rätt skydd. Copy/
Paste uppfyller detta genom att se till att persondata aldrig behandlas av externa parter och inte lagras
i onödan. Känsliga uppgifter är flyktiga i systemet: de passerar genom minnet, blir maskade, och
sparas inte rått på disk. Endast den anonymiserade versionen går vidare. För mig som journalist
betyder det att jag vågar använda verktyget även på case där källor måste hållas hemliga. Jag kan t.ex.
klistra in ett dokument med konfidentiella personuppgifter – Copy/Paste markerar “[PERSON_A]”,
“[PERSON_B]” istället för namnen när texten skickas för summering. Så fort utkastet är klart och jag
stänger ärendet, kan originaldokumentet raderas från systemets aktiva minne. Därmed minimeras
risken att någon obehörig skulle komma åt de riktiga namnen via AI-verktyget. Det är datasäkerhet i
praktiken, inte bara i policydokument.
Jämför detta med att en del reportrar idag frestas att köra t.ex. en hel intervjutext genom ChatGPT för
att få en summering. Det må ge en bra sammanfattning, men man har då de facto skickat upp intervjun
till en extern molntjänst där den kan lagras och i värsta fall dyka upp i träningen av modellen. Sådant har
redan hänt – företag har råkat läcka affärshemligheter till OpenAI på det viset. Många redaktioner är
därför på sin vakt. I en SJF-enkät 2018 erkände 68% av reportrarna att de inte ens visste om en
källskyddspolicy fanns på redaktionen, och kunskapen om kryptering var låg . Nu har
medvetenheten ökat, men det behövs verktyg som gör det lätt att göra rätt. Copy/Paste är ett exempel
som bygger in säkra rutiner (som anonymisering) så att journalisten per default jobbar på ett sätt som
inte äventyrar källskyddet. Istället för att lita på att alla reportrar manuellt maskar text innan de
använder AI (en osäker och tidskrävande metod), sköts det automagiskt.
Utöver persondata så är systemet internt hostat, vilket generellt ger bättre kontroll. Alla komponenter
kan köras på företagets egna servrar eller i ett privat moln under strikta avtal. Inget material hamnar på
obehöriga servrar. Det minskar angreppsytan för både hackerintrång och oförutsedd datadelning. För
journalistiken som bransch är detta vitalt – vi har sett hur t.ex. övervakningsprogram hos stora
mediehus har skapat debatt om reportrarnas egna filer loggas och hur det kan hota källskyddet . I
en värld där säkerhet ibland krockar med integritet ger Copy/Paste ett exempel på hur man kan
balansera det: man kan ha loggar och pipeline som bevakar flöden och ändå inte logga de känsliga
detaljerna.
En annan aspekt är ”Right to be forgotten” – att data inte ska sparas längre än nödvändigt. Systemet
sägs vara byggt med insikten att ingen råtext lagras på lång sikt. Så om en källa skulle höra av sig och
ångra att de delat viss info, finns det inte hundra kopior spridda i AI-systemet; det är rensat eller i värsta
fall spårbart för radering. Detta skiljer sig från t.ex. mailkedjor eller utspridda personliga anteckningar
där kontrollen är sämre.
I korthet uppfyller Copy/Paste de högsta kraven på datasäkerhet för ett redaktionellt verktyg: det
skyddar identiteter, det lagrar minimalt och det låter inte extern AI suga åt sig våra rådata. För en
journalist minskar det oron att teknikanvändning skulle råka bryta det förtroendekontrakt man har med
sina källor. Vi får nytta av ny teknik utan att riskera att hamna i fängelse för röjande av källa (vilket lagen
faktiskt stadgar som maxstraff för allvarliga källskyddsbrott !). Den tryggheten är ovärderlig.
22
23
24
7
Begränsningar och utmaningar
Ingen lösning är perfekt. Även om Copy/Paste låter som ett kraftfullt verktyg finns förstås potentiella
begränsningar och utmaningar att vara medveten om:
Kvaliteten på AI-utkasten varierar med underlaget: Om input-datan är tunn, motsägelsefull
eller av låg kvalitet, kan inte ens bästa AI skapa ett bra utkast. Det gamla uttrycket “garbage in,
garbage out” gäller. Copy/Paste kan flagga osäkra punkter, men den kan missa nyanser eller
underbetona något viktigt som inte framgick tydligt i källorna. Journalisten måste fortfarande
tänka kritiskt: Har jag hela bilden? Om t.ex. bara polisens kortfattade notis ligger till grund,
kanske AI-utkastet blir väldigt rudimentärt. Det sparar ändå tid, men journalistens erfarenhet
avgör om mer research behövs.
Ingen ersättning för egen research eller intervjuer: Verktyget kan inte ringa källor, ställa
följdfrågor eller känna av om någon ljuger. Det ger ett utkast baserat på befintlig info, men
journalistikens kärna – att skaffa fram ny information och originella vinklar – måste
reportrarna fortsatt göra själva. Copy/Paste kan i värsta fall ge en falsk känsla av att “storyn är
klar” när AI-texten är klar, trots att man kanske borde jaga en kommentar eller faktakolla hos en
extern part. Det kräver disciplin att se AI-utkastet som ett startunderlag, inte slutresultatet.
Redaktionen måste vara tydlig internt att egna kontroller, rundringningar och omdöme
fortfarande gäller. Annars finns en risk att verktyget passiviserar vissa mindre erfarna reportrar.
Hård sanning: lat journalistik kan inte trollas bort med AI.
Inlärningskurva och förändrat arbetssätt: Att införa Copy/Paste innebär att reportrar och
redaktörer behöver vänja sig vid ett nytt arbetssätt. Inte alla journalister är teknikvana eller
positiva till att ändra rutiner. Några kanske upplever att det är snabbare att "göra på sitt vanliga
sätt". Det krävs utbildning och kulturförändring för att utnyttja verktyget maximalt. Ledningen
måste förankra varför källhänvisningar, anonymisering etc. är viktigt och hur man använder
gränssnittet effektivt. I jobbeskrivningen framgår att man söker en utvecklare som kan “sälja in
MVP-arbetssättet” och jobba nära användarna – klokt, för utan buy-in från journalisterna riskerar
verktyget att stå oanvänt trots sina fördelar.
Underhåll och tekniskt ansvar: När man bygger ett eget AI-kontrollrum tar man på sig
ansvaret för dess driftsäkerhet och uppdateringar. AI- och datafältet rör sig snabbt. Modeller kan
bli inaktuella eller få nya versioner som är bättre. Nya datakällor kan tillkomma (t.ex. fler RSSflöden,
eller kanske att bevaka sociala medier). Systemet behöver kontinuerlig kärlek: buggar
fixas, anonymiseringsmönster uppdateras (t.ex. nya personnamn, slang osv måste kännas igen),
och pipeline måste skalas om datamängden ökar. Detta kräver att Stampen avsätter teknisk
kompetens löpande. Finns risken att om nyckelpersoner slutar, så faller kunskapen? I en mindre
organisation är det en risk att ha interna specialverktyg. Hård sanning: magin som sparar tid i
vardagen kan snabbt utebli om inte verktyget hålls i trim.
Risk för ökad homogenitet om alla använder samma verktyg: Om majoriteten av utkasten
får en liknande AI-behandling, kan det påverka språklig variation och angreppssätt. Agnes
Stenbom varnar för konformitet – AI som tränats på historiska texter kan återskapa etablerade
narrativ och vändningar på bekostnad av originalitet . Copy/Paste, om än internt tränad eller
inställd, kan tänkas driva fram ett visst standardformat i utkasten (t.ex. nyhetsbyrå-ton). Det är
inte nödvändigtvis dåligt, men redaktionen bör vara medveten och aktivt uppmuntra reportrar
att sätta egen prägel i omskrivningen. Verktyget ska vara katalysator för kreativitet, inte en
mall för likriktning . Detta hanteras förmodligen bäst genom redaktionell feedback:
•
•
•
•
•
20
25
8
cheferna kan jämföra AI-utkast och sluttext och säkerställa att journalistens röst och vinkeln de
valt verkligen skiner igenom i slutversionen.
Begränsad domänkunskap hos AI:n: Generativa modeller kan mycket, men ibland brister de i
specialistkunskap eller lokal kännedom. Stampens verktyg verkar dock använda lokala databaser
och artiklar som bas, likt Spinoza som fylldes med lokalt innehåll . Om Copy/Paste integreras
med t.ex. retriever-arkiv eller interna arkiv, kan den bli bättre på lokala fakta. Men initialt kanske
den är mest generell. Journalister som skriver om smala ämnen (säg kommunpolitikens
byggregler) får inte förlita sig på att AI:n kan allt – den kanske missar interna referenser eller
felstavade namn på kommunala bolag. Så även här: kolla alltid så att alla namn och fakta
verkligen stämmer med egna källor. AI:n kan ha anonymiserat ett namn och sedan råkat göra det
generiskt i texten, vilket man behöver återinföra korrekt. Slutsats: AI-stödet minskar rutinarbete
men eliminerar inte behovet av ämneskunniga reportrar.
Etiska överväganden vid publicering: Om en artikel till stor del bygger på AI-genererat
underlag, hur transparent ska man vara mot läsarna? Detta är en debatt under utveckling. Vissa
hävdar att man bör flagga AI-assistans för läsarna av princip, andra menar att så länge allt är
korrekt och genomgånget av en människa spelar det ingen roll – texten är journalistens arbete.
Copy/Paste ger redaktionen möjlighet att vara ärliga internt, men man bör troligen utarbeta en
policy externt också: t.ex. publicera en metodruta om AI användes, eller inte? Det är inget fel i att
använda AI, men publikförtroende är skört. Tänk på fallet med Sports Illustrated som fick kraftig
kritik när det avslöjades att de publicerat AI-skrivna artiklar under falska bylines . Copy/Paste i
sig undviker falska bylines då det är reportrarnas namn som står och de har redigerat texten,
men principen om öppenhet kan ändå vara bra att adressera. Detta är mer en policyfråga för
ledningen än en teknisk begränsning, men det är en utmaning att hantera.
I slutändan är dessa utmaningar hanterbara genom kloka rutiner och medvetenhet. Ingen automatik
befriar journalisten från ansvar – det är nog den hårdaste men viktigaste sanningen. Copy/Paste tar
hand om mycket, men lämnar med rätta det yttersta ansvaret i reportrarnas händer. Om man inför
systemet med den insikten och utbildning i ryggsäcken, kan man undvika fallgroparna och mestadels
skörda fördelarna.
Slutsats
Copy/Paste – Editorial AI Control Room representerar ett ambitiöst försök att integrera AI i det
journalistiska arbetet på journalistikens egna villkor. Från en senior journalists perspektiv är det
imponerande hur verktyget angriper två stora problem samtidigt: tidsbristen och
förtroendeproblematiken med AI. Genom att spara tid på bevakning, research och utkastskrivning
adresserar det den hårda realiteten på dagens redaktioner – att färre reportrar ska hantera mer
information snabbare än någonsin. Samtidigt går det inte på kompromiss med grundprinciperna: varje
fakta ska kunna beläggas, integriteten skyddas, och slutkontrollen ligger hos människan.
Den ärliga sanningen är att ingen journalistisk mirakelmaskin existerar. Copy/Paste kommer inte att
skriva Pulitzervinnande reportage åt oss, och det kommer inte göra oss överflödiga. Vad det kan göra är
att befria oss från en del av det slitiga rutinjobbet som stjäl tid och energi, så att vi istället kan fokusera
på det som gör journalistiken meningsfull – att gräva fram sanningen, berätta den väl och göra
skillnad i samhället. Verktyget är utformat just för detta syfte: förstärk journalistiken, urholka den inte.
Det stämmer överens med insikten i branschen att AI ska vara som en kollega i kulisserna, inte en
konkurrent .
•
26
•
27
8
9
I värdet av sparad tid ligger inte bara kvantitet (att producera fler artiklar snabbare) utan också kvalitet:
tid som frigörs kan användas för dubbla källor, extra intervjuer eller mer eftertanke. Med Copy/Paste
kan en redaktion i bästa fall både öka sin output och höja sin noggrannhet, eftersom AI:n hjälper till att
hålla reda på fakta och källor konsekvent. I en idealisk framtid ser jag framför mig att sådana här
system blir lika självklara på redaktioner som internetuppkoppling – en del av infrastrukturen.
Dock, som med alla verktyg, avgörs nyttan av hur vi använder det. Ansvaret, kreativiteten och
dömandet ligger fortsatt hos oss journalister. Copy/Paste verkar förstå detta och har designats för att
samspela med journalistens arbete, inte automatisera bort det mänskliga elementet. Det är en sund
inställning. Faktum är att projekt som Spinoza och initiativ från nyhetsorganisationer världen över pekar
mot just denna modell: AI utvecklat i samråd med journalister och med etiska ramar, är inte bara
möjligt utan också nödvändigt för framtiden .
Min slutsats är att Copy/Paste är ett genuint nyttigt verktyg ur ett journalistperspektiv. Det ger
påtaglig tidsvinst i vardagen och stärker den journalistiska processen genom spårbarhet. “Hård sanning
utan fluff” här är att om verktyget håller vad konceptet lovar, kan det höja både tempot och
tillförlitligheten i nyhetsproduktionen – en sällsynt kombination. Men för att det ska realisera sin fulla
potential måste redaktionen omfamna det med rätt förhållningssätt: se det som stöd, inte krycka, och
fortsätta prioritera källkritik och eget omdöme i alla lägen. I så fall är Copy/Paste ett steg framåt som
kan hjälpa oss journalister att göra mer av det vi är bäst på – granska, informera och berätta – med
lite mindre stress över monotona måsten. Det är en ärlig förbättring i arbetsflödet, inte en hype-bubbla.
Som utvärderare och journalist kan jag säga: det här verktyget är byggt på journalistikens premisser, och
det märks. Det svarar mot behoven vi faktiskt har idag i nyhetsarbetet. Och ja – det sparar tid på riktigt.
Källor:
- Reportrar utan gränser, "Nytt AI-verktyg för nyhetsredaktioner" – om AI-projektet Spinoza och hur AI kan
spara tid på översättning, transkribering och sammanfattning .
- Sider.ai, "Hur kan journalister använda AI i sitt arbete?" – praktisk handbok om AI i redaktionen, som
betonar snabbare research, sammanfattningar och källhänvisningar med bibehållen noggrannhet
.
- KTH Nyheter, "Etisk AI-användning inom journalistik kan stärka demokratin" – intervju med Agnes
Stenbom om vikten av transparens, mänskligt ansvar och att AI frigör tid för mer kvalificerat
journalistiskt arbete .
- AP News, "Wyoming reporter caught using AI to create fake quotes, stories" – nyhet om riskerna med
oansvarig AI-användning och hur AP och andra infört restriktioner; belyser behovet av källkontroll och
policy .
- Sveriges Tidskrifter, "Superviktig guide – Så skyddar du källorna digitalt" – om journalistiskt källskydd,
lagkrav och behovet av säkra rutiner i digital miljö .
Nytt AI-verktyg för nyhetsredaktioner - Reportrar utan gränser
https://www.reportrarutangranser.se/nytt-ai-verktyg-for-nyhetsredaktioner/
Hur kan journalister använda AI i sitt arbete? En praktisk handbok för den
moderna nyhetsredaktionen
https://sider.ai/sv/blog/ai-tools/how-can-journalists-use-ai-in-their-work-a-practical-playbook-for-the-modern-newsroom
Etisk AI-användning inom journalistik kan stärka demokratin | KTH
https://www.kth.se/om/nyheter/centrala-nyheter/etisk-ai-anvandning-inom-journalistik-kan-starka-demokratin-1.1371061
Wyoming reporter caught using AI to create fake quotes, stories | AP News
https://apnews.com/article/artificial-intelligence-reporter-resigns-journalism-ed076e2f276d9811f3b9ba051a03b7ae
28
1 8
2
3
4 16
7 5 6
24 22
1 8 10 14 18 26 28
2 3 9 11 15 17
4 16 20 25
5 6 7 21 27
10
12 Ways Journalists Use AI Tools in the Newsroom - Twipe
https://www.twipemobile.com/12-ways-journalists-use-ai-tools-in-the-newsroom/
Superviktig guide för publicister – Så skyddar du källorna digitalt - Sveriges Tidskrifter
https://sverigestidskrifter.se/artikel/superviktig-guide-for-publicister-sa-skyddar-du-kallorna-digitalt/
12 13 19
22 23 24
11