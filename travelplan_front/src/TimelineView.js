import React, { useState, useMemo } from 'react';
import { Rnd } from 'react-rnd';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Add as AddIcon,
  DragIndicator as DragIcon,
  AccessTime as TimeIcon,
  InfoOutlined as InfoIcon,
} from '@mui/icons-material';

const CELL_WIDTH = 120;   // 时间格子宽度
const CELL_HEIGHT = 80;   // 时间格子高度
const HEADER_HEIGHT = 40; // 标题高度
const DAY_START_HOUR = 7; // 一天的开始时间（7:00 AM）
const DAY_END_HOUR = 22;  // 一天的结束时间（10:00 PM）

const TimelineView = ({ startDate, endDate, selectedPlaces }) => {
    const { days, timeSlots, start } = useMemo(() => {
        const start = startDate instanceof Date ? startDate : new Date(startDate);
        const end = endDate instanceof Date ? endDate : new Date(endDate);
        const days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1);
        
        // 生成时间刻度（7:00 AM - 10:00 PM）
        const timeSlots = Array.from(
          { length: DAY_END_HOUR - DAY_START_HOUR }, 
          (_, i) => {
            const hour = i + DAY_START_HOUR;
            return hour < 12 
              ? `${hour}:00 AM` 
              : hour === 12 
                ? `12:00 PM` 
                : `${hour - 12}:00 PM`;
          }
        );
    
        return { days, timeSlots, start };
      }, [startDate, endDate]);

    const [selectedEvent, setSelectedEvent] = useState(null);
    const [events, setEvents] = useState([{
        id: 1,
        title: 'Example Place',
        startTime: '9:00 AM',
        endTime: '11:00 AM',
        day: 0,
        position: {
          x: (9 - DAY_START_HOUR) * CELL_WIDTH,
          y: HEADER_HEIGHT, // 从标题行下方开始
        },
        duration: 2,
      }]);
    
      const positionToTime = (x) => {
        const hourIndex = Math.floor(x / CELL_WIDTH);
        const hour = hourIndex + DAY_START_HOUR;
        
        return hour < 12 
          ? `${hour}:00 AM` 
          : hour === 12 
            ? '12:00 PM' 
            : `${hour - 12}:00 PM`;
      };
    
      // 工具函数：计算天数和时间
      const calculateDayAndTime = (x, y) => {
        // 减去标题行高度后计算天数
        const day = Math.floor((y - HEADER_HEIGHT) / CELL_HEIGHT);
        const hourIndex = Math.floor(x / CELL_WIDTH);
        const startHour = hourIndex + DAY_START_HOUR;
    
        return {
          day,
          startTime: positionToTime(x),
          endTime: positionToTime(x + (CELL_WIDTH * 2))
        };
      };
    
      // 修改拖动处理函数，考虑标题行高度
      const handleDragStop = (eventId) => (e, d) => {
        const nearestX = Math.floor(d.x / CELL_WIDTH) * CELL_WIDTH;
        // 减去标题行高度后再计算对齐位置
        const nearestY = HEADER_HEIGHT + (Math.floor((d.y - HEADER_HEIGHT) / CELL_HEIGHT) * CELL_HEIGHT);
        
        // 确保 x 位置在有效范围内
        const maxX = (timeSlots.length - events.find(e => e.id === eventId).duration) * CELL_WIDTH;
        const boundedX = Math.max(0, Math.min(nearestX, maxX));
        
        // 确保 y 位置在有效范围内（考虑标题行高度）
        const maxY = HEADER_HEIGHT + (days - 1) * CELL_HEIGHT;
        const minY = HEADER_HEIGHT; // 最小值是标题行的底部
        const boundedY = Math.max(minY, Math.min(nearestY, maxY));
    
        const { day, startTime, endTime } = calculateDayAndTime(boundedX, boundedY);
    
        setEvents(prevEvents => 
          prevEvents.map(event => 
            event.id === eventId 
              ? {
                  ...event,
                  day,
                  startTime,
                  endTime,
                  position: {
                    x: boundedX,
                    y: boundedY
                  }
                }
              : event
          )
        );
      };

  return (
    <Box sx={{ 
        display: 'flex', 
        gap: 0,
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        overflow: 'hidden',
      }}>
        {/* 左侧日期列表 */}
        <Box sx={{ 
          width: 180,
          flexShrink: 0,
          borderRight: 1,
          borderColor: 'divider',
          bgcolor: 'background.default',
        }}>
          {/* 左上角标题单元格 */}
          <Box sx={{ 
            height: HEADER_HEIGHT,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            px: 2,
            bgcolor: 'background.paper',
          }}>
            <Typography variant="subtitle2" color="text.secondary">
              Schedule
            </Typography>
          </Box>

        {/* 日期列表 */}
        <Box>
          {Array.from({ length: days }).map((_, index) => {
            const currentDate = new Date(start);
            currentDate.setDate(start.getDate() + index);
            
            return (
              <Box
                key={index}
                sx={{
                  height: CELL_HEIGHT,
                  borderBottom: 1,
                  borderColor: 'divider',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  px: 2,
                  bgcolor: 'background.paper',
                }}
              >
                <Typography variant="subtitle2" color="primary">
                  Day {index + 1}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {currentDate.toLocaleDateString('en-US', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric'
                  })}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>

      {/* 时间轴区域 - 调整为占满剩余空间 */}
      <Box sx={{ 
        flex: 1,
        overflow: 'auto',
        position: 'relative' // 确保定位正确
      }}>
        {/* 时间刻度标题行 */}
        <Box sx={{ 
          display: 'flex',
          height: HEADER_HEIGHT,
          position: 'sticky',
          top: 0,
          backgroundColor: 'background.paper',
          zIndex: 2,
          borderBottom: 1,
          borderColor: 'divider'
        }}>
          {timeSlots.map((time) => (
            <Box
              key={time}
              sx={{
                width: CELL_WIDTH,
                minWidth: CELL_WIDTH,
                height: HEADER_HEIGHT,
                borderRight: 1,
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: 'background.paper',
              }}
            >
              <Typography variant="body2" color="text.secondary">
                {time}
              </Typography>
            </Box>
          ))}
        </Box>

        {/* 时间格子 */}
        <Box sx={{ 
          position: 'relative',
          minHeight: days * CELL_HEIGHT
        }}>
          {/* 时间格子背景 */}
          {Array.from({ length: days }).map((_, dayIndex) => (
            <Box
              key={dayIndex}
              sx={{
                display: 'flex',
                height: CELL_HEIGHT,
                borderBottom: 1,
                borderColor: 'divider'
              }}
            >
              {timeSlots.map((_, timeIndex) => (
                <Box
                  key={timeIndex}
                  sx={{
                    width: CELL_WIDTH,
                    minWidth: CELL_WIDTH,
                    borderRight: 1,
                    borderColor: 'divider'
                  }}
                />
              ))}
            </Box>
          ))}

          {/* 事件块 */}
          {events.map(event => (
            <Rnd
              key={event.id}
              default={{
                x: event.position.x,
                y: event.position.y,
                width: CELL_WIDTH * event.duration,
                height: CELL_HEIGHT - 1,
              }}
              size={{
                width: CELL_WIDTH * event.duration,
                height: CELL_HEIGHT - 1,
              }}
              position={{
                x: event.position.x,
                y: event.position.y
              }}
              dragGrid={[CELL_WIDTH, CELL_HEIGHT]}
              bounds="parent"
              enableResizing={false}
              onDragStop={handleDragStop(event.id)}
              dragHandleClassName="drag-handle"
            >
          <Paper
            elevation={3}
            sx={{
              width: '100%',
              height: '100%',
              bgcolor: 'primary.light',
              color: 'white',
              p: 1,
              display: 'flex',
              alignItems: 'center',
              userSelect: 'none',
              boxSizing: 'border-box',
              '&:hover': {
                bgcolor: 'primary.main',
              },
            }}
          >
              <Box 
                className="drag-handle" 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  cursor: 'grab',
                  '&:active': { cursor: 'grabbing' }
                }}
              >
                <DragIcon sx={{ fontSize: 20, mr: 1 }} />
              </Box>

              <Box sx={{ flex: 1, overflow: 'hidden' }}>
                <Typography variant="subtitle2" noWrap>
                  {event.title}
                </Typography>
                <Typography variant="caption" noWrap>
                  {event.startTime} - {event.endTime}
                </Typography>
              </Box>

              <IconButton 
                size="small" 
                sx={{ color: 'white' }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedEvent({
                    ...event,
                    time: `${event.startTime} - ${event.endTime}`,
                  });
                }}
              >
                <InfoIcon />
              </IconButton>
            </Paper>
          </Rnd>
        ))}
      </Box>
      </Box>

      {/* 详情对话框 - 更新显示内容 */}
      <Dialog
        open={Boolean(selectedEvent)}
        onClose={() => setSelectedEvent(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: 'primary.light', color: 'white' }}>
          {selectedEvent?.title}
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TimeIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography>
                {selectedEvent?.startTime} - {selectedEvent?.endTime}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Day {selectedEvent?.day + 1}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedEvent(null)}>Close</Button>
          <Button variant="contained">Edit</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TimelineView;