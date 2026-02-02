from odoo import http, SUPERUSER_ID
from odoo.http import request
from datetime import datetime, timedelta
import json


class RegistroPresenzeController(http.Controller):

    @http.route(
        '/api/v2/registro_presenze',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )

    #test odoo endpoint
    def get_v2_registro_presenze(self, viaggio=None, dataDa=None, dataA=None, **kwargs):
        if not viaggio:
            return request.make_response(
                json.dumps({'error': 'Parametro "viaggio" mancante.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )
        if not dataDa:
            return request.make_response(
                json.dumps({'error': 'Parametro "dataDa" mancante.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )
        if not dataA:
            dataA = dataDa

        try:
            dt_da = datetime.strptime(dataDa, '%Y-%m-%d').date()
            dt_a = datetime.strptime(dataA, '%Y-%m-%d').date()
        except ValueError:
            return request.make_response(
                json.dumps({'error': 'Le date devono essere nel formato YYYY-MM-DD.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        if dt_da > dt_a:
            return request.make_response(
                json.dumps({'error': 'dataDa non può essere successiva a dataA.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        viaggio_rec = request.env['rette.viaggio'].sudo().search([('id_intranet', '=', viaggio)], limit=1)

        if not viaggio_rec:
            return request.make_response(
                json.dumps({'error': f'Viaggio con id_intranet={viaggio} non trovato.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        days_list = []
        current_date = dt_da
        while current_date <= dt_a:
            days_list.append(current_date)
            current_date += timedelta(days=1)

        schema_base = {
            "locale": "it",
            "title": "Presenza giornaliera",
            "logoPosition": "right",
            "pages": [
                {
                    "name": "page1",
                    "elements": [
                        {
                            "type": "boolean",
                            "name": "presenza",
                            "title": "Presente\\Assente",
                            "isRequired": True,
                            "labelTrue": "Presente",
                            "labelFalse": "Assente",
                            "valueTrue": "P",
                            "valueFalse": "A",
                            "swapOrder": True
                        },
                        {
                            "type": "radiogroup",
                            "name": "presenza_tipo",
                            "visibleIf": "{presenza} = P",
                            "title": "Tipo di presenza",
                            "resetValueIf": "{presenza} = 'A'",
                            "requiredIf": "{presenza} = P",
                            "choices": []
                        },
                        {
                            "type": "radiogroup",
                            "name": "assenza_tipo",
                            "visibleIf": "{presenza} = A",
                            "title": "Tipo di assenza",
                            "resetValueIf": "{presenza} = P",
                            "requiredIf": "{presenza} = A",
                            "choices": []
                        },
                        {
                            "type": "panel",
                            "name": "Servizi",
                            "visibleIf": "{presenza} anyof ['P', 'A']",
                            "showQuestionNumbers": "off",
                            "elements": []
                        }
                    ]
                }
            ],
            "calculatedValues": [
                {
                    "name": "attendance_slug",
                    "expression": "{presenza} + {presenza_tipo} + {assenza_tipo}",
                    "includeIntoResult": True
                }
            ],
            "showTitle": False,
            "showPageTitles": False,
            "showCompletedPage": False,
            "showQuestionNumbers": "off",
            "checkErrorsMode": "onValueChanged",
            "completeText": "Salva",
            "previewText": "Conferma",
            "editText": "Modifica",
            "questionsOnPageMode": "singlePage",
            "showPreviewBeforeComplete": "off",
            "widthMode": "responsive"
        }

        results = []
        all_rate_rels = []
        rate_ids = request.env['journey.tariffa.line.rel'].sudo().search([('journey_id', '=', viaggio_rec.id), ('journey_tariffa_line_rel_state', '!=', 'closed')])
        for rate in rate_ids:

            all_rate_rels.extend(rate)
        all_variation_rels = rate_ids.with_user(SUPERUSER_ID).mapped('tariffa_variazione_ids')

        default_groups = request.env['rette.tariffa.gruppo'].sudo().search([
            ('default', '=', True),
            ('active', '=', True)
        ])


        def get_gruppi_per_data(d):
            pres_codes = set()
            abs_codes = set()
            oth_codes = set()

            presence_list = []
            absence_list = []
            other_list = []

            for g in default_groups:
                if g.type == 'present':
                    pres_codes.add(g.product_code)
                    presence_list.append({"value": g.product_code, "text": g.name})
                elif g.type == 'absent':
                    abs_codes.add(g.product_code)
                    absence_list.append({"value": g.product_code, "text": g.name})
                elif g.type in ('other', 'other_p', 'other_a'):
                    if g.product_code not in oth_codes:
                        oth_codes.add(g.product_code)
                        other_list.append({
                            "product_code": g.product_code,
                            "name": g.name,
                            "bool_type": False,
                            "group_type": g.type
                        })

            for line in all_rate_rels:
                if line.rate_from_date and line.rate_from_date > d:
                    continue
                if line.rate_to_date and line.rate_to_date < d:
                    continue

                for group in line.group_ids:
                    grp = group
                    tarif = line.tariffa_line_id.rate_id
                    if not grp or not grp.active:
                        continue

                    if grp.type == 'present':
                        if grp.product_code not in pres_codes:
                            pres_codes.add(grp.product_code)
                            presence_list.append({"value": grp.product_code, "text": grp.name})
                    elif grp.type == 'absent':
                        if grp.product_code not in abs_codes:
                            abs_codes.add(grp.product_code)
                            absence_list.append({"value": grp.product_code, "text": grp.name})
                    elif grp.type in ('other', 'other_p', 'other_a'):
                        if grp.product_code not in oth_codes:
                            oth_codes.add(grp.product_code)
                            other_list.append({
                                "product_code": grp.product_code,
                                "name": grp.name,
                                "bool_type": tarif.bool_type_registro,
                                "group_type": grp.type
                            })

            for var in all_variation_rels:
                grp = var.group_id
                if not grp or not grp.active:
                    continue
                if var.start_date > d:
                    continue

                if grp.type == 'absent' and grp.product_code not in abs_codes:
                    abs_codes.add(grp.product_code)
                    absence_list.append({"value": grp.product_code, "text": grp.name})
                elif grp.type in ('other', 'other_p', 'other_a') and grp.product_code not in oth_codes:
                    oth_codes.add(grp.product_code)
                    other_list.append({
                        "product_code": grp.product_code,
                        "name": grp.name,
                        "bool_type": False,
                        "group_type": grp.type
                    })

            return presence_list, absence_list, other_list

        for day in days_list:
            presence_list, absence_list, other_list = get_gruppi_per_data(day)
            daily_schema = json.loads(json.dumps(schema_base))
            elements = daily_schema["pages"][0]["elements"]

            el_presenza = next((e for e in elements if e.get('name') == 'presenza_tipo'), None)
            if el_presenza:
                el_presenza["choices"] = presence_list

            el_assenza = next((e for e in elements if e.get('name') == 'assenza_tipo'), None)
            if el_assenza:
                el_assenza["choices"] = absence_list

            el_panel = next((e for e in elements if e.get('type') == 'panel' and e.get('name') == 'Servizi'), None)
            if el_panel:
                panel_elements = []
                for alt in other_list:
                    el = {}
                    if alt['bool_type']:
                        el = {
                            "type": "boolean",
                            "name": alt["product_code"],
                            "title": alt["name"],
                            "defaultValue": "0",
                            "isRequired": True,
                            "valueTrue": "1",
                            "valueFalse": "0"
                        }
                    else:
                        el = {
                            "type": "text",
                            "name": alt["product_code"],
                            "title": alt["name"],
                            "isRequired": True,
                            "inputType": "number",
                            "min": 0
                        }
                    if alt.get("group_type") == "other_p":
                        el["visibleIf"] = "{presenza} = 'P'"
                    elif alt.get("group_type") == "other_a":
                        el["visibleIf"] = "{presenza} = 'A'"
                    panel_elements.append(el)

                el_panel["elements"] = panel_elements

            if not el_panel["elements"]:
                # Se non ci sono elementi del panel servii rimuove la chiave:
                del daily_schema["pages"][0]['elements'][3]

            show_dayly_schema = False
            if daily_schema["pages"][0]["elements"][1]['choices'] != []:
                #Mostra il JSON del giorno valorizzato SOLO se ci sono degli oggetti di tipologia presenza
                show_dayly_schema = True

            record_day = {
                "viaggio": viaggio_rec.id_intranet,
                "dataDa": str(day),
                "dataA": str(day),
                "schema": daily_schema if show_dayly_schema else {}
            }
            results.append(record_day)

        response_body = json.dumps(results, ensure_ascii=False)
        return request.make_response(
            response_body,
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )

    @http.route(
        '/api/v1/registro_presenze',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def get_registro_presenze(self, viaggio=None, dataDa=None, dataA=None, **kwargs):
        if not viaggio:
            return request.make_response(
                json.dumps({'error': 'Parametro "viaggio" mancante.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )
        if not dataDa:
            return request.make_response(
                json.dumps({'error': 'Parametro "dataDa" mancante.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )
        if not dataA:
            dataA = dataDa

        try:
            dt_da = datetime.strptime(dataDa, '%Y-%m-%d').date()
            dt_a = datetime.strptime(dataA, '%Y-%m-%d').date()
        except ValueError:
            return request.make_response(
                json.dumps({'error': 'Le date devono essere nel formato YYYY-MM-DD.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        if dt_da > dt_a:
            return request.make_response(
                json.dumps({'error': 'dataDa non può essere successiva a dataA.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        viaggio_rec = request.env['rette.viaggio'].sudo().search([('id_intranet', '=', viaggio)], limit=1)

        if not viaggio_rec:
            return request.make_response(
                json.dumps({'error': f'Viaggio con id_intranet={viaggio} non trovato.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        days_list = []
        current_date = dt_da
        while current_date <= dt_a:
            days_list.append(current_date)
            current_date += timedelta(days=1)

        schema_base = {
            "locale": "it",
            "title": "Presenza giornaliera",
            "logoPosition": "right",
            "pages": [
                {
                    "name": "page1",
                    "elements": [
                        {
                            "type": "boolean",
                            "name": "presenza",
                            "title": "Presente\\Assente",
                            "isRequired": True,
                            "labelTrue": "Presente",
                            "labelFalse": "Assente",
                            "valueTrue": "P",
                            "valueFalse": "A",
                            "swapOrder": True
                        },
                        {
                            "type": "radiogroup",
                            "name": "presenza_tipo",
                            "visibleIf": "{presenza} = P",
                            "title": "Tipo di presenza",
                            "resetValueIf": "{presenza} = 'A'",
                            "requiredIf": "{presenza} = P",
                            "choices": []
                        },
                        {
                            "type": "radiogroup",
                            "name": "assenza_tipo",
                            "visibleIf": "{presenza} = A",
                            "title": "Tipo di assenza",
                            "resetValueIf": "{presenza} = P",
                            "requiredIf": "{presenza} = A",
                            "choices": []
                        },
                        {
                            "type": "panel",
                            "name": "Servizi",
                            "visibleIf": "{presenza} anyof ['P', 'A']",
                            "showQuestionNumbers": "off",
                            "elements": []
                        }
                    ]
                }
            ],
            "calculatedValues": [
                {
                    "name": "attendance_slug",
                    "expression": "{presenza} + {presenza_tipo} + {assenza_tipo}",
                    "includeIntoResult": True
                }
            ],
            "showTitle": False,
            "showPageTitles": False,
            "showCompletedPage": False,
            "showQuestionNumbers": "off",
            "checkErrorsMode": "onValueChanged",
            "completeText": "Salva",
            "previewText": "Conferma",
            "editText": "Modifica",
            "questionsOnPageMode": "singlePage",
            "showPreviewBeforeComplete": "off",
            "widthMode": "responsive"
        }

        results = []
        all_rate_rels = []
        rate_ids = viaggio_rec.rate_ids
        for rate in rate_ids:
            if (not rate.rate_from_date or rate.rate_from_date <= dt_da) and (not rate.rate_to_date or rate.rate_to_date >= dt_a):
                all_rate_rels.extend(rate.rate_id)
        all_variation_rels = viaggio_rec.contract_ids.mapped('tariffa_variazione_ids')

        default_groups = request.env['rette.tariffa.gruppo'].sudo().search([
            ('default', '=', True),
            ('active', '=', True)
        ])


        # rate_ids = request.env['rate.journey.rel'].sudo().browse(viaggio_rec.rate_ids.ids)
        # contract_ids = request.env['rette.contratto']
        # for rate in rate_ids:
        #     if (not rate.rate_from_date or rate.rate_from_date <= dt_da):
        #         all_rate_rels.extend(rate)
        #         contract_ids |= rate.contract_id

        # default_groups = request.env['rette.tariffa.gruppo'].sudo().search([
        #     ('default', '=', True),
        #     ('active', '=', True)
        # ])
        #
        # # Variazione tariffa
        # all_variation_rels = []
        # variations = contract_ids.with_user(SUPERUSER_ID).mapped('tariffa_variazione_ids')
        # for v in variations:
        #     for t in v.rette_contratto_tariffa_id:
        #         if t in all_rate_rels:
        #             all_variation_rels.append(t)



        def get_gruppi_per_data(d):
            pres_codes = set()
            abs_codes = set()
            oth_codes = set()

            presence_list = []
            absence_list = []
            other_list = []

            for g in default_groups:
                if g.type == 'present':
                    pres_codes.add(g.product_code)
                    presence_list.append({"value": g.product_code, "text": g.name})
                elif g.type == 'absent':
                    abs_codes.add(g.product_code)
                    absence_list.append({"value": g.product_code, "text": g.name})
                elif g.type in ('other', 'other_p', 'other_a'):
                    if g.product_code not in oth_codes:
                        oth_codes.add(g.product_code)
                        other_list.append({
                            "product_code": g.product_code,
                            "name": g.name,
                            "bool_type": False,
                            "group_type": g.type
                        })

            for line in all_rate_rels:
                contract = line.contract_id
                if contract.from_date and contract.from_date > d:
                    continue
                if contract.to_date and contract.to_date < d:
                    continue
                # if line.rate_from_date and line.rate_from_date > d:
                #     continue
                # if line.rate_to_date and line.rate_to_date < d:
                #     continue

                grp = line.group_id
                tarif = line.rate_id
                if not grp or not grp.active:
                    continue

                if grp.type == 'present':
                    if grp.product_code not in pres_codes:
                        pres_codes.add(grp.product_code)
                        presence_list.append({"value": grp.product_code, "text": grp.name})
                elif grp.type == 'absent':
                    if grp.product_code not in abs_codes:
                        abs_codes.add(grp.product_code)
                        absence_list.append({"value": grp.product_code, "text": grp.name})
                elif grp.type in ('other', 'other_p', 'other_a'):
                    if grp.product_code not in oth_codes:
                        oth_codes.add(grp.product_code)
                        other_list.append({
                            "product_code": grp.product_code,
                            "name": grp.name,
                            #"bool_type": tarif.rate_id.bool_type_registro,
                            "bool_type": tarif.bool_type_registro,
                            "group_type": grp.type
                        })

            for var in all_variation_rels:
                grp = var.group_id
                if not grp or not grp.active:
                    continue
                if grp.type == 'absent' and grp.product_code not in abs_codes:
                    abs_codes.add(grp.product_code)
                    absence_list.append({"value": grp.product_code, "text": grp.name})
                elif grp.type in ('other', 'other_p', 'other_a') and grp.product_code not in oth_codes:
                    oth_codes.add(grp.product_code)
                    other_list.append({
                        "product_code": grp.product_code,
                        "name": grp.name,
                        "bool_type": False,
                        "group_type": grp.type
                    })

            return presence_list, absence_list, other_list

        for day in days_list:
            presence_list, absence_list, other_list = get_gruppi_per_data(day)
            daily_schema = json.loads(json.dumps(schema_base))
            elements = daily_schema["pages"][0]["elements"]

            el_presenza = next((e for e in elements if e.get('name') == 'presenza_tipo'), None)
            if el_presenza:
                el_presenza["choices"] = presence_list

            el_assenza = next((e for e in elements if e.get('name') == 'assenza_tipo'), None)
            if el_assenza:
                el_assenza["choices"] = absence_list

            el_panel = next((e for e in elements if e.get('type') == 'panel' and e.get('name') == 'Servizi'), None)
            if el_panel:
                panel_elements = []
                for alt in other_list:
                    el = {}
                    if alt['bool_type']:
                        el = {
                            "type": "boolean",
                            "name": alt["product_code"],
                            "title": alt["name"],
                            "defaultValue": "0",
                            "isRequired": True,
                            "valueTrue": "1",
                            "valueFalse": "0"
                        }
                    else:
                        el = {
                            "type": "text",
                            "name": alt["product_code"],
                            "title": alt["name"],
                            "isRequired": True,
                            "inputType": "number",
                            "min": 0
                        }
                    if alt.get("group_type") == "other_p":
                        el["visibleIf"] = "{presenza} = 'P'"
                    elif alt.get("group_type") == "other_a":
                        el["visibleIf"] = "{presenza} = 'A'"
                    panel_elements.append(el)

                el_panel["elements"] = panel_elements

            if not el_panel["elements"]:
                #Se non ci sono elementi del panel servii rimuove la chiave:
                del daily_schema["pages"][0]['elements'][3]

            show_dayly_schema = False
            if len(daily_schema["pages"][0]["elements"]) > 3:
                show_dayly_schema = True
            if daily_schema["pages"][0]["elements"][1]['choices'] != []:
                show_dayly_schema = True
            if daily_schema["pages"][0]["elements"][2]['choices'] != []:
                show_dayly_schema = True

            record_day = {
                "viaggio": viaggio_rec.id_intranet,
                "dataDa": str(day),
                "dataA": str(day),
                "schema": daily_schema if show_dayly_schema else {}
            }
            results.append(record_day)

        response_body = json.dumps(results, ensure_ascii=False)
        return request.make_response(
            response_body,
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )
