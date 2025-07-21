from flask_restful import Resource

class Sample(Resource):
    def get(self):
        """
        This is a sample GET request.
        ---
        responses:
          200:
            description: A sample message
            schema:
              id: Sample
              properties:
                message:
                  type: string
                  default: This is a sample response.
        """
        return {'message': 'This is a sample response.'}
