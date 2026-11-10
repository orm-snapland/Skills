# קריאות Snapland ישראל — רק מה שהמצב הקיים צריך

טען כלים עם `tool_search("Snapland Israel ...")`. מחזיר רק Spain → הקונקטור כבוי או דורש התחברות:
`search_mcp_registry(["snapland","israel"])` → `suggest_connectors`.
`get_property` דורש `fields`; `INVALID_FIELD_SELECTION` מחזיר רשימת `allowed` — לוקחים משם.

| מטרה | קריאה |
|---|---|
| זיהוי | `search_cadastral_local_id(israel, "6106_399")` → `parcel_geometry` |
| נכס | `get_entity_by_snap_id(fields=address,neighborhood,municipality_name,cadastral_section_number,parcel_number,local_id,registered_area_sqm,area_sqm,land_use,has_buildings,related_buildings,related_construction_permits)` — `unlocks.page=false` = נעול |
| מבנים | `get_property(buildings, bui-…, fields=geometry,year_built,floors_above_ground,height_m,has_pillar_floor,area_sqm,total_floor_area_sqm,primary_use)` — מבנה־מבנה |
| היתרים על החלקה | `get_entity_relationship_page(linked-construction-permits, fields=permit_number,application_number,status,permit_type,work_type,issue_date,completion_date,authorized_units,authorized_floors,authorized_area_sqm)` |
| עסקאות על החלקה | `transactions-on-parcel` — שטח היחידה בעסקה הוא הקירוב הטוב ביותר לחציון הטאבו |
| זכויות למסלול | `linked-build-rights` עם `building_option` — רשומות `"בנין קיים"` שייכות לחיזוק ותוספת, `"בנין חדש"` להריסה ובנייה |

## מאיפה כל מספר בטבלה
| שורה | מקור ראשון | גיבוי |
|---|---|---|
| טביעת רגל | `buildings.area_sqm` או שטח הפוליגון מ-`geometry` | מדידה גרפית מהיתר |
| קומות · כניסות | `floors_above_ground`, `has_pillar_floor` | היתר (`authorized_floors`), ספירה בתצ"א |
| יח"ד | נסח, יחידות דיוור, `authorized_units` בהיתר | ספירת תיבות דואר או מרפסות בחזית |
| ברוטו | חישוב: טביעת רגל × קומות למגורים | `total_floor_area_sqm` כשקיים, כערך שני |
| שטח שירות | כלל אצבע 15 מ"ר לקומה לכל כניסה | מדידת גרעין מתשריט |
| גודל ממוצע נטו | חישוב | מדידה, או חציון עסקאות |
| סבירות מול טאבו | `transactions-on-parcel` / נסח | — |
| מדידה | `permit-measurement` על תשריט ההיתר | מודד |

`total_floor_area_sqm` ב-Snapland לא תמיד מלא ולא תמיד מבחין בין ברוטו לשטח עיקרי. כשהוא קיים וסותר את החישוב —
רושמים `source: "סותר"` עם שני הערכים, ולא בוחרים צד בשקט.
