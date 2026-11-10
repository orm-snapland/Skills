# נתונים — קריאות, שדות, מלכודות, תצ"א

## קריאות Snapland ישראל
טען כלים עם `tool_search("Snapland Israel ...")`. אם החיפוש מחזיר רק Spain — הקונקטור כבוי או דורש התחברות מחדש:
`search_mcp_registry(["snapland","israel"])` → `suggest_connectors([uuid])`.

| מטרה | קריאה | הערות |
|---|---|---|
| זיהוי | `search_cadastral_local_id(israel, "6106_399")` | מחזיר `parcel_geometry` — זה הפוליגון למפות ולמעטפת |
| מעטפת הנכס | `get_entity_by_snap_id(fields=address,neighborhood,municipality_name,cadastral_section_number,parcel_number,local_id,registered_area_sqm,area_sqm,ownership_type,land_use,has_buildings,related_buildings,related_build_rights,related_construction_permits)` | `unlocks.page=false` = נעול, לא ריק |
| זכויות | `get_entity_relationship_page(linked-build-rights, size=40, fields=plan_number,level,source_pipeline,rights_category,building_option,area_sqm,area_sqm_source_text,raw_unit_source_text,area_type,area_location,units_count,floors_count,coverage,lot_area_for_rights_sqm,apartment_size,building_height,roof_exit_rooms,balconies,parking_note)` | ערכים מספריים חסרים? `get_property(build-rights, snap_id, fields=planning_zone_name,planning_zone_type,floors_count,coverage_source_text,rear_setback_m,side_setback_m,front_setback_m,balcony_allowance,note)` על רשומות `israel_5000_rova*` ו-`telaviv_rights` |
| מבנה | `get_property(buildings, bui-…, fields=geometry,year_built,floors_above_ground,height_m,has_pillar_floor,area_sqm,total_floor_area_sqm)` | |
| תכניות | `filtered-plans-in-process` · `filtered-plans-approved` (q=מספר תכנית — הרשימה ארוכה) | |
| היתרים | `linked-construction-permits` · `nearby-construction-permits` (size 25–50, בלי q; `filters` לא מסנן — מסננים בסקריפט) עם `fields=permit_number,application_number,status,permit_type,work_type,application_date,issue_date,start_date,completion_date,distance_m,authorized_units,authorized_floors,authorized_area_sqm,land_parcel_snap_ids` | היתר שהושלם בסביבה = כיול לו"ז רישוי. **מלאי ומכירות:** `scripts/permit_supply.py` — יח"ד לפי שלב, חודשי רישוי, עסקאות לפני/אחרי ההיתר, קומות |
| עסקאות להיתרים | `transactions-in-area` עם `land_parcel_snap_id` בשדות (בלעדיו אין התאמה להיתר) | עסקה מעל 400 מ"ר = קרקע / שטר קומבינציה, לא דירה |
| גובה מאושר | `authorized_floors` בהיתר; ריק → מבנה שנבנה אחרי ההיתר (`buildings`: floors_above_ground, height_m, year_built) — מתויג "בנוי"; אין → "חסר" | גובה במטרים לא קיים בהיתר ב-Snapland; לא ממציאים |
| עסקאות | `transactions-on-parcel` · `transactions-in-area` (size 100) | ממוין לפי מרחק; 100 מספיק לרוב |
| הליכים | `linked-appraisal-decisions` · `linked-appeals` · `filtered-protected-buildings` | |
| סביבה | `get_property_nearby_layers` | אזור הכרזה, עתיקות, זיהום, מטרו, פטור חניה, תמ"א 38 |
| שכנים | `search_entity(parcels, geo={"bounding_box":...}, fields=local_id,address,geometry, size=40)` | למפות |

`get_property` דורש `fields`; `INVALID_FIELD_SELECTION` מחזיר רשימת `allowed` — קח משם.

## היררכיית זכויות
| `level` / `source_pipeline` | מעמד |
|---|---|
| `parcel` / `telaviv_rights` | מאושר — בר־מימוש. "ראה הערה" = נגזר מהמעטפת |
| `PLANNING_ZONE` / `israel_5000_rova*` | תכנית רובע — פרמטרים (קומות, תכסית, נסיגות, הערות נוסחה) |
| `PLANNING_ZONE` / `israel_5000_ta5000_*`, `ta5500_*`, `mitar_*` | שכבה / בהליך — לא זכות |
רשומות `building_option="בנין קיים"` שייכות למסלול חיזוק ותוספת; `"בנין חדש"` — להריסה ובנייה.

## מלכודות קבועות (לטבלה בסעיף 10)
| מלכודת | בדיקה |
|---|---|
| "ראה הערה" | אין שטח מספרי → מחשבים מהמעטפת ומתייגים `חישוב` |
| שכבות רובע כפולות | אותה חלקה "בתחום" וגם "מחוץ" לאזור ההכרזה → הכרע לפי `white_city_zone.distance_m` |
| גודל מגרש מינימלי | 0 / 0.5 / 1.5 בשכבות 5000 = דונם, לא מ"ר |
| גובה מול קומות | גובה ÷ קומות מחוץ ל-2.6–3.5 → לא בונים על הגובה (קומת עמודים / מבנה גג) |
| יתרת בנייה | שווה למקדם × מגרש? → סך, לא יתרה |
| עסקאות על החלקה | `land_parcel_snap_id` תואם ו-`distance_m=0` |
| מספר דירות | שטח בנוי ÷ יח"ד מול גודל טיפוסי לאזור ולתקופה; Snapland לרוב בלי `units_count` לבניין |
| רישום כפול | אותה תכנית/היתר פעמיים (למשל הודעת 77–78 וטיוטה) |

## תצ"א לתקציר המנהלים
- **מקור מועדף:** GIS עיריית ת"א, שירות האורתופוטו (`gisn.tel-aviv.gov.il`), שכבת "2026"; פוליגון משכבת החלקות (524).
- **קרדיט חובה:** "תצ"א: אורתופוטו GIS עיריית תל אביב (gisn.tel-aviv.gov.il), שכבת "2026" — קובץ המקור Tel_Aviv_2022_08.sid, ולכן ייתכן שהצילום מאוגוסט 2022; תאריך הצילום אינו ודאי. גבול החלקה: אותו GIS, שכבת החלקות (524)."
- **מגבלות ידועות:** רשת הקונטיינר חוסמת `gisn.tel-aviv.gov.il` ו-`server.arcgisonline.com` (`host_not_allowed`) — נדרש allowlist ע"י בעל ארגון. `get_property_satellite_image` / `get_static_image` של Snapland מרנדרים בשרת אך הקונקטור נכשל בפענוח הבינארי. Claude in Chrome — רק אם מחובר.
- **גיבוי:** צילום מסך שהמשתמש מעלה (עם גבול ואורכי צלעות). לעולם לא מציירים תצ"א מזויפת; בלי תמונה — מציבים את מפת הנכס הווקטורית ומציינים זאת בכיתוב.

---
## v2 — תוספות (גוברות על האמור לעיל)
- **לכל מבנה קיים:** `get_property(buildings, fields=floors_above_ground,total_floor_area_sqm,primary_use,year_built,has_pillar_floor,height_m,geometry)`.
  בטבלה: קומות · שטח (מ"ר) · שימוש · שנה.
- **תכניות ברדיוס 500 מ' וטבעת 50 מ':** `references/planning.md`.
- **שכנים ודרכים:** בשליפת השכנים כלול `land_use`; חלקות "דרך" גובלות קובעות את החזיתות (`front_edges`).
- **סתירות:** כשמקור אחר (מסמך, מזמין, מדידה) סותר את Snapland — רושמים `source: "סותר"`, `value` (הערך שבשימוש),
  `alt` (הערך השני) ו-`alt_source`. בדוח: תג "סותר" בשורת הנתון עם שני הערכים, ושורה בטבלת הסתירות בנספח א'. **לא בסעיף 10.**
  כשהמזמין מתקן נתון — הערך המתוקן בשימוש, והתג בשורה הוא "החלטה" עם ציון התיקון.
- **מכירות קבלן:** `tx_stats_v2` מזהה גם סדרות (≥6 עסקאות בחלקה בתוך חצי שנה) ומקבל `extra_new` לפרויקטים שזוהו ידנית
  (למשל אשכול יומי לפני 2024). עסקאות מעבר לגבול העירוני — נכללות ומסומנות.
- **מחיר לפי שימוש:** אם לעסקאות יש שדה שימוש — `use_key`; פחות מ-6 עסקאות לשימוש → `ask_user=True` → עצירה 5.
