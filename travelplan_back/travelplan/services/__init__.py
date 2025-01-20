# services/__init__.py
from .schedule_service import ScheduleService

# 创建全局服务实例
schedule_service = ScheduleService()

__all__ = ['schedule_service']