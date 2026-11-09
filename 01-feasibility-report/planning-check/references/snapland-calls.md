# קריאות Snapland ישראל — רק מה שהבדיקה התכנונית צריכה

טען כלים עם `tool_search("Snapland Israel ...")`. מחזיר רק Spain → הקונקטור כבוי / דורש התחברות: `search_mcp_registry(["snapland","israel"])` → `suggest_connectors`.
`get_property` דורש `fields`; `INVALID_FIELD_SELECTION` מחזיר רשימת `allowed` — לוקחים משם.

| מטרה | קריאה |
|---|---|
| זיהוי | `search_cadastral_local_id(israel, "6106_399")` → `parcel_geometry` |
| נכס | `get_entity_by_snap_id(fields=address,neighborhood,municipality_name,cadastral_section_number,parcel_number,local_id,registered_area_sqm,area_sqm,land_use,related_build_rights)` — `unlocks.page=false` = נעול |
| זכויות | `get_entity_relationship_page(linked-build-rights, size=40, fields=plan_number,level,source_pipeline,rights_category,building_option,area_sqm,area_sqm_source_text,units_count,floors_count,coverage,lot_area_for_rights_sqm,building_height)` |
| פרמטרי רובע | `get_property(build-rights, snap_id, fields=planning_zone_name,planning_zone_type,floors_count,coverage_source_text,rear_setback_m,side_setback_m,front_setback_m,note)` על רשומות `israel_5000_rova*` / `telaviv_rights` |
| תכניות על החלקה | `filtered-plans-approved` · `filtered-plans-in-process` (q=מספר תכנית — הרשימה ארוכה) |
| מדיניות | `policy_documents`, `planning_notes` מתוך הזכויות |
| רדיוס 500 מ' | `sources.md` §3 |
| הליכים | `linked-appraisal-decisions` · `linked-appeals` · `filtered-protected-buildings` |
| שכבות סביבה | `get_property_nearby_layers` — אזור הכרזה, עתיקות, מטרו, פטור חניה, תמ"א 38 |
| טבעת 50 מ' | `search_entity(parcels, geo={"bounding_box":…}, fields=local_id,address,geometry,land_use, size=40)`; מבנים: `get_property(buildings, fields=floors_above_ground,primary_use,year_built,height_m)` |

## מלכודות
| מלכודת | בדיקה |
|---|---|
| "ראה הערה" | אין שטח מספרי → `חישוב` (מעטפת), לא `מערכת` |
| שכבות רובע כפולות | "בתחום" וגם "מחוץ" לאזור ההכרזה → לפי `white_city_zone.distance_m` |
| גודל מגרש מינימלי | 0 / 0.5 / 1.5 = דונם |
| גובה מול קומות | גובה ÷ קומות מחוץ ל-2.6–3.5 → לא בונים על הגובה |
| יתרת בנייה | שווה למקדם × מגרש → סך, לא יתרה |
| רישום כפול | אותה תכנית פעמיים (הודעת 77–78 וטיוטה) → שורה אחת |
