const newsData = [
    {
        "id": 1764017680,
        "date": "24/11/2025",
        "category": "geopolitica",
        "author": "La Redazione",
        "title": "Brasile, Lula in Mozambico riceve una laurea honoris causa",
        "excerpt": "...",
        "body": "Analisi momentaneamente non disponibile.",
        "imageIcon": "fa-globe-europe",
        "imageReal": "",
        "link": "https://www.ansa.it/sito/notizie/mondo/americalatina/2025/11/24/brasile-lula-in-mozambico-riceve-una-laurea-honoris-causa_9fb057b6-584c-4457-aa0c-aced12990738.html"
    },
    {
        "id": 1764016998,
        "date": "24/11/2025",
        "category": "cronaca",
        "author": "Max V.",
        "title": "#AccadeOggi",
        "excerpt": "I principali avvenimenti previsti per la giornata",
        "imageIcon": "fa-user-secret",
        "link": "https://www.ansa.it/sito/notizie/cronaca/2025/11/24/accadeoggi_dd38a7d3-309c-4e12-a6b9-d7b1590e0cf6.html"
    },
    {
        "id": 1764017000,
        "date": "24/11/2025",
        "category": "geopolitica",
        "author": "Max V.",
        "title": "Paraguay e Israele firmano un memorandum sulla Difesa",
        "excerpt": "Visita ad Asunci\u00f3n del ministro degli Esteri Gideon Sa'ar",
        "imageIcon": "fa-globe-europe",
        "link": "https://www.ansa.it/sito/notizie/mondo/americalatina/2025/11/24/paraguay-e-israele-firmano-un-memorandum-sulla-difesa_0d12cba6-b68d-470b-9370-5b8ff91c89ae.html"
    },
    {
        "id": 1764017004,
        "date": "24/11/2025",
        "category": "arte",
        "author": "Il Corvo",
        "title": "'Moda e bellezza dal Friuli' protagonista a Palazzo Metternich",
        "excerpt": "A Vienna sfilano talento e tradizione della Regione",
        "imageIcon": "fa-film",
        "link": "https://www.ansa.it/sito/notizie/cultura/moda/2025/11/24/moda-e-bellezza-dal-friuli-protagonista-a-palazzo-metternich_6ee1ae52-ef6a-4a1c-a2c3-14b6dea6662e.html"
    },
    {
        "category": "cronaca",
        "title": "++ 19enne ucciso a Napoli non era l'obiettivo dell'agguato ++",
        "excerpt": "Killer 15enne voleva colpire un amico. Ha agito da solo a piedi...",
        "imageIcon": "fa-user-secret",
        "link": "https://www.ansa.it/sito/notizie/cronaca/2025/11/24/-19enne-ucciso-a-napoli-non-era-lobiettivo-dellagguato-_272237bf-d194-4533-bf12-02d65406ff37.html"
    },
    {
        "category": "cronaca",
        "title": "Casa nel bosco: Ministero, rispettato l'obbligo scolastico",
        "excerpt": "'Attraverso l'educazione domiciliare'...",
        "imageIcon": "fa-user-secret",
        "link": "https://www.ansa.it/sito/notizie/cronaca/2025/11/24/casa-nel-bosco-ministero-rispettato-lobbligo-scolastico_5c3393ac-5b28-44c9-bbe3-0d422bd7c6b2.html"
    },
    {
        "category": "geopolitica",
        "title": "Von der Leyen, 'solo Kiev pu\u00f2 decidere sul suo esercito'",
        "excerpt": "'I territori e la sovranit\u00e0 dell'Ucraina vanno rispettati'...",
        "imageIcon": "fa-globe-europe",
        "link": "https://www.ansa.it/sito/notizie/mondo/europa/2025/11/24/von-der-leyen-solo-kiev-puo-decidere-sul-suo-esercito_98d68ba1-efa4-43e4-be0a-c60aadce3e7c.html"
    },
    {
        "category": "geopolitica",
        "title": "Putin, 'piano Usa pu\u00f2 essere base per soluzione pacifica'",
        "excerpt": "'Cos\u00ec come \u00e8 stato presentato a Mosca'...",
        "imageIcon": "fa-globe-europe",
        "link": "https://www.ansa.it/sito/notizie/mondo/europa/2025/11/24/putin-piano-usa-puo-essere-base-per-soluzione-pacifica_73c9c82e-88c1-4fc5-9328-5e34e8a75578.html"
    },
    {
        "category": "tech",
        "title": "Apple risarcir\u00e0 proprietari di MacBook per le tastiere difettose",
        "excerpt": "Giudice Usa ha dato via libera all'intesa da 50 milioni di dollari...",
        "imageIcon": "fa-microchip",
        "link": "https://www.ansa.it/sito/notizie/tecnologia/hitech/2023/05/30/apple-risarcira-proprietari-di-macbook-per-le-tastiere-difettose_ce9214c7-b68d-4d8e-ad5f-7bd5bd04ecbe.html"
    },
    {
        "category": "tech",
        "title": "L'inventore di Internet Tim Berners-Lee alla Fiera di Rimini",
        "excerpt": "Ospite l'eccezione a Wmf - We Male Future, dal 15 al 17 giugno...",
        "imageIcon": "fa-microchip",
        "link": "https://www.ansa.it/sito/notizie/tecnologia/internet_social/2023/05/30/linventore-di-internet-tim-berners-lee-alla-fiera-di-rimini_8d846c97-938c-40d3-a479-5100edfc4344.html"
    },
    {
        "category": "sport",
        "title": "Prometeon presente alla Dakar 2026 con Martin Mac\u00edk Jr.",
        "excerpt": "Il truck sar\u00e0 equipaggiato con pneumatici Serie 02 Rally...",
        "imageIcon": "fa-running",
        "link": "https://www.ansa.it/sito/notizie/sport/altrisport/2025/11/24/prometeon-presente-alla-dakar-2026-con-martin-macik-jr._e7579cba-7518-489b-8b63-1ece8f44be16.html"
    },
    {
        "category": "sport",
        "title": "Premier:scuse Guardiola per reazione furibonda dopo ko Newcastle",
        "excerpt": "Tecnico ha avuto anche alterco con cameraman togliendogli cuffie...",
        "imageIcon": "fa-running",
        "link": "https://www.ansa.it/sito/notizie/sport/calcio/2025/11/24/premierscuse-guardiola-per-reazione-furibonda-dopo-ko-newcastle_550c64f2-36f7-430c-9c19-2ccf849ece09.html"
    },
    {
        "category": "arte",
        "title": "Addio a Jimmy Cliff, la voce del reggae",
        "excerpt": "Star di The Harder They Come, aveva 81 anni...",
        "imageIcon": "fa-film",
        "link": "https://www.ansa.it/sito/notizie/cultura/musica/2025/11/24/addio-a-jimmy-cliff-la-voce-del-reggae_4f713ad5-7e5b-4efd-8800-9b61fe49a604.html"
    },
    {
        "category": "arte",
        "title": "Prima nazionale a Bologna per Castelli di Rabbia di Baricco",
        "excerpt": "All'Arena del Sole dal 27 novembre con regia di Valter Malosti...",
        "imageIcon": "fa-film",
        "link": "https://www.ansa.it/sito/notizie/cultura/teatro/2025/11/24/prima-nazionale-a-bologna-per-castelli-di-rabbia-di-baricco_ca533116-0646-48f6-94ab-56be72a8213a.html"
    },
    {
        "category": "difesa",
        "title": "Analisi Strategica: Scenari 2025",
        "excerpt": "Report esclusivo del Sottobosco sulle nuove tecnologie militari e l'impatto globale.",
        "imageIcon": "fa-shield-alt",
        "link": "https://www.rid.it/"
    }
];