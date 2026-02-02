from odoo import http
from odoo.http import request
import json


class SectorAPIController(http.Controller):

    @http.route(
        '/api/v1/sector',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def get_sector(self, limit=None, offset=None, **kwargs):
        """
        API endpoint to retrieve sector.sector records

        Parameters:
            - limit (optional): Number of records per page (default: 500)
            - offset (optional): Pagination offset (default: 0)

        Returns:
            JSON object with:
            - total_count: Total number of records matching the criteria
            - limit: Applied limit
            - offset: Applied offset
            - records: List of sector.sector records
        """

        # 4. Validate and parse pagination parameters
        try:
            page_limit = int(limit) if limit else 500
            if page_limit <= 0:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "limit" deve essere un numero positivo.'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )
        except ValueError:
            return request.make_response(
                json.dumps({'error': 'Il parametro "limit" deve essere un numero intero.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        try:
            page_offset = int(offset) if offset else 0
            if page_offset < 0:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "offset" deve essere un numero non negativo.'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )
        except ValueError:
            return request.make_response(
                json.dumps({'error': 'Il parametro "offset" deve essere un numero intero.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        # 6. Query data using sudo() for public access
        try:
            # Get total count of records matching the criteria
            total_count = request.env['sector.sector'].sudo().search_count([])

            # Check if any records exist
            if total_count == 0:
                return request.make_response(
                    json.dumps({
                        'warning': 'Nessun record trovato con i criteri specificati.',
                        'total_count': 0,
                        'limit': page_limit,
                        'offset': page_offset,
                        'records': []
                    }, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json; charset=utf-8')]
                )

            # Get paginated records ordered by id ascending
            lines = request.env['sector.sector'].sudo().search_read(
                [], # Aggiunto un domain vuoto
                fields=None,  # Return all fields
                order='id asc', # Modificato per evitare errori se 'date' non esiste
                limit=page_limit,
                offset=page_offset
            )

            # 7. Build response with metadata
            result = {
                'total_count': total_count,
                'limit': page_limit,
                'offset': page_offset,
                'records': lines
            }

            # 8. Return JSON response with proper encoding
            # Use default=str to handle datetime and other non-serializable objects
            response_body = json.dumps(result, ensure_ascii=False, default=str)
            return request.make_response(
                response_body,
                headers=[('Content-Type', 'application/json; charset=utf-8')]
            )

        except Exception as e:
            # Handle any unexpected errors
            return request.make_response(
                json.dumps({'error': f'Errore durante il recupero dei dati: {str(e)}'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )