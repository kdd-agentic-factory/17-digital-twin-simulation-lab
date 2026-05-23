from digital_twin_lab.routers.health import router as health_router
from digital_twin_lab.routers.parts import router as parts_router
from digital_twin_lab.routers.recommendations import router as recommendations_router
from digital_twin_lab.routers.reports import router as reports_router
from digital_twin_lab.routers.scenarios import router as scenarios_router
from digital_twin_lab.routers.setup import router as setup_router
from digital_twin_lab.routers.simulations import router as simulations_router
from digital_twin_lab.routers.tires import router as tires_router
from digital_twin_lab.routers.what_if import router as what_if_router

all_routers = [
    health_router,
    scenarios_router,
    simulations_router,
    what_if_router,
    setup_router,
    tires_router,
    parts_router,
    recommendations_router,
    reports_router,
]
