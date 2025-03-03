# evaluation/run_evaluation.py

import asyncio
import django
django.setup()

from evaluation.evaluate import run_evaluation

# Test data (Paris example)
test_places = [
    {
        "geometry": {
            "location": {
                "lat": 48.8566,
                "lng": 2.3522
            }
        },
        "place_id": "hotel_paris_center",
        "name": "Paris Center Hotel",
        "types": ["lodging", "hotel"],
        "rating": 4.5,
        "user_ratings_total": 2000,
        "vicinity": "Central Paris",
        "formatted_address": "Central Paris, France",
        "opening_hours": {"open_now": True},
        "price_level": 3
    },
    {
        "geometry": {
            "location": {
                "lat": 48.8584,
                "lng": 2.2945
            }
        },
        "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
        "name": "Eiffel Tower",
        "types": ["tourist_attraction", "point_of_interest"],
        "rating": 4.6,
        "user_ratings_total": 375000,
        "vicinity": "Champ de Mars",
        "formatted_address": "Champ de Mars, Paris, France",
        "opening_hours": {"open_now": True},
        "price_level": 2
    },
    {
        "geometry": {
            "location": {
                "lat": 48.8629,
                "lng": 2.3386
            }
        },
        "place_id": "ChIJ3Qp9_FJu5kcRv3QrZZl4qqk",
        "name": "Le Bistrot Vivienne",
        "types": ["restaurant", "point_of_interest", "food"],
        "rating": 4.4,
        "user_ratings_total": 1500,
        "vicinity": "Galerie Vivienne",
        "formatted_address": "4 Rue des Petits Champs, Paris, France",
        "opening_hours": {"open_now": True},
        "price_level": 2
    },
    {
        "geometry": {
            "location": {
                "lat": 48.8606,
                "lng": 2.3376
            }
        },
        "place_id": "ChIJATr1n-Fx5kcRjQb6q6cdQDY",
        "name": "Louvre Museum",
        "types": ["museum", "tourist_attraction", "point_of_interest"],
        "rating": 4.7,
        "user_ratings_total": 270000,
        "vicinity": "Rue de Rivoli",
        "formatted_address": "Rue de Rivoli, Paris, France",
        "opening_hours": {"open_now": True},
        "price_level": 2
    }
]

if __name__ == "__main__":
    asyncio.run(run_evaluation(
        places=test_places,
        start_date="2024-02-08",
        end_date="2024-02-10",
        transport_mode="walking",
        num_random_solutions=100  # Generate 100 random solutions for comparison
    ))