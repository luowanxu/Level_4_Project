import React, { useState, useEffect, useMemo } from 'react';
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
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  DragIndicator as DragIcon,
  AccessTime as TimeIcon,
  InfoOutlined as InfoIcon,
} from '@mui/icons-material';
import axios from 'axios';

const CELL_WIDTH = 120;   // 时间格子宽度
const CELL_HEIGHT = 80;   // 时间格子高度
const HEADER_HEIGHT = 40; // 标题高度
const DAY_START_HOUR = 9; // 一天的开始时间（9:00 AM）
const DAY_END_HOUR = 21;  // 一天的结束时间（9:00 PM）

const TimelineView = ({ startDate, endDate, selectedPlaces, onEventsUpdate }) => {
    // TimelineView.js 中的 useMemo 部分
    const { days, timeSlots, start } = useMemo(() => {
      const start = startDate instanceof Date ? startDate : new Date(startDate);
      const end = endDate instanceof Date ? endDate : new Date(endDate);
      const days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1);
      
      // 生成时间刻度（9:00 AM - 8:00 PM）
      const timeSlots = Array.from(
        { length: 12 }, // 从9点到20点，共12小时
        (_, i) => {
          const hour = i + DAY_START_HOUR;
          if (hour === 12) {
            return '12:00 PM';
          } else if (hour > 12) {
            return `${hour - 12}:00 PM`;
          } else {
            return `${hour}:00 AM`;
          }
        }
      );
    
      return { days, timeSlots, start };
    }, [startDate, endDate]);

    const [selectedEvent, setSelectedEvent] = useState(null);
    const [events, setEvents] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    
    // 添加这个 useEffect 在 events 状态定义后面
    useEffect(() => {
      const initializeTimeline = async () => {
        if (!startDate || !endDate || !selectedPlaces.length) return;
    
        setLoading(true);
        try {
          const response = await axios.post('/api/cluster-places/', {
            places: selectedPlaces,
            startDate: startDate.toISOString().split('T')[0],
            endDate: endDate.toISOString().split('T')[0]
          });
    
          if (response.data.success) {
            setEvents(response.data.events);
            onEventsUpdate?.(response.data.events);  // 添加这一行
            setError(null);
          } else {
            setError(response.data.error || 'Failed to create itinerary');
          }
        } catch (error) {
          setError(error.response?.data?.error || 'Failed to connect to server');
        } finally {
          setLoading(false);
        }
      };
    
      initializeTimeline();
    }, [startDate, endDate, selectedPlaces, onEventsUpdate]);  // 添加 onEventsUpdate 到依赖数组
    
    const positionToTime = (x) => {
      const hourIndex = Math.floor(x / CELL_WIDTH);
      const hour = hourIndex + DAY_START_HOUR;
      
      // 转换为12小时制
      if (hour === 0 || hour === 12) {
        return `12:00 ${hour === 0 ? 'AM' : 'PM'}`;
      } else if (hour > 12) {
        return `${hour - 12}:00 PM`;
      } else {
        return `${hour}:00 AM`;
      }
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
        // 防止事件冒泡
        e.stopPropagation();
        
        const cellPosition = {
          x: Math.round(d.x / CELL_WIDTH) * CELL_WIDTH,
          y: Math.round(d.y / CELL_HEIGHT) * CELL_HEIGHT
        };
      
        const maxX = (timeSlots.length - events.find(e => e.id === eventId).duration) * CELL_WIDTH;
        const maxY = (days - 1) * CELL_HEIGHT;
      
        const boundedX = Math.max(0, Math.min(cellPosition.x, maxX));
        const boundedY = Math.max(0, Math.min(cellPosition.y, maxY));
      
        const day = Math.floor(boundedY / CELL_HEIGHT);
      
        setEvents(prevEvents => {
          const updatedEvents = prevEvents.map(event => 
            event.id === eventId 
              ? {
                  ...event,
                  day,
                  startTime: positionToTime(boundedX),
                  endTime: positionToTime(boundedX + (CELL_WIDTH * event.duration)),
                  position: {
                    x: boundedX,
                    y: boundedY
                  }
                }
              : event
          );
          // 通知父组件事件已更新
          onEventsUpdate?.(updatedEvents);
          return updatedEvents;
        });
      };


    const handleDrag = (e, d) => {
      // 防止事件冒泡
      e.stopPropagation();
    };



    const getTypeStyles = (place) => {
      const type = place?.types?.includes('lodging') ? 'hotel' 
                 : place?.types?.includes('tourist_attraction') ? 'attraction'
                 : place?.types?.includes('restaurant') ? 'restaurant'
                 : 'default';
    
      switch (type) {
        case 'restaurant':
          return {
            backgroundColor: '#FF9800',
            hoverColor: '#F57C00',
            dialogColor: '#FFB74D'
          };
        case 'attraction':
          return {
            backgroundColor: '#4CAF50',
            hoverColor: '#388E3C',
            dialogColor: '#81C784'
          };
        case 'hotel':
          return {
            backgroundColor: '#2196F3',
            hoverColor: '#1976D2',
            dialogColor: '#64B5F6'
          };
        default:
          return {
            backgroundColor: '#9C27B0',
            hoverColor: '#7B1FA2',
            dialogColor: '#BA68C8'
          };
      }
    };



  if (loading) {
    return (
      <Box sx={{ 
        p: 3, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center' 
      }}>
        <CircularProgress />
      </Box>
    );
  }
  // 显示错误信息
  if (error) {
    return (
      <Box sx={{ 
        p: 3, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        color: 'error.main'
      }}>
        <Typography>{error}</Typography>
      </Box>
    );
  }
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
          position: 'relative',
          display: 'flex',
          flexDirection: 'column'
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
        
          {/* 时间格子区域 */}
          <Box sx={{ 
              position: 'relative',
              height: days * CELL_HEIGHT,
              flexGrow: 1,
              zIndex: 0  // 确保正确的层级关系
            }}>
              {/* 网格背景 */}
              <Box sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: 'none',  // 让背景网格不影响鼠标事件
                zIndex: 1
              }}>
              {Array.from({ length: days }).map((_, dayIndex) => (
                <Box
                  key={dayIndex}
                  sx={{
                    position: 'absolute',
                    top: dayIndex * CELL_HEIGHT,
                    left: 0,
                    right: 0,
                    height: CELL_HEIGHT,
                    display: 'flex',
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
                        height: '100%',
                        borderRight: 1,
                        borderColor: 'divider'
                      }}
                    />
                  ))}
                </Box>
              ))}
            </Box>
        
            {/* 事件块 */}
            <Box sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 2
            }}></Box>
            {events.map(event => (
              <Rnd
              key={event.id}
              default={{
                x: event.position.x,
                y: event.position.y,
                width: CELL_WIDTH * event.duration,
                height: CELL_HEIGHT
              }}
              size={{
                width: CELL_WIDTH * event.duration,
                height: CELL_HEIGHT
              }}
              position={event.position}
              dragGrid={[CELL_WIDTH, CELL_HEIGHT]}
              bounds="parent"
              enableResizing={false}
              onDragStop={handleDragStop(event.id)}
              onDrag={handleDrag}
              dragHandleClassName="drag-handle"
              style={{
                cursor: 'move',
                zIndex: 3
              }}
            >
              <Paper
                elevation={3}
                sx={{
                  width: '100%',
                  height: '100%',
                  bgcolor: getTypeStyles(event.place).dialogColor,  // 使用更淡的颜色
                  color: 'text.primary',  // 改为深色文字以提高可读性
                  p: 1,
                  display: 'flex',
                  alignItems: 'center',
                  cursor: 'move',
                  userSelect: 'none',
                  boxSizing: 'border-box',
                  '&:hover': {
                    bgcolor: getTypeStyles(event.place).backgroundColor,  // hover 时使用深色
                    color: 'white',  // hover 时文字改为白色
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
        <DialogTitle 
          sx={{ 
            bgcolor: selectedEvent ? getTypeStyles(selectedEvent.place).dialogColor : 'primary.light',
            color: 'text.primary'
          }}
        >
          {selectedEvent?.title}
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TimeIcon 
                sx={{ 
                  mr: 1, 
                  color: selectedEvent ? getTypeStyles(selectedEvent.place).backgroundColor : 'primary.main' 
                }} 
              />
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
          <Button 
            onClick={() => setSelectedEvent(null)}
            sx={{ 
              color: selectedEvent ? getTypeStyles(selectedEvent.place).backgroundColor : 'primary.main' 
            }}
          >
            Close
          </Button>
          <Button 
            variant="contained"
            sx={{
              bgcolor: selectedEvent ? getTypeStyles(selectedEvent.place).backgroundColor : 'primary.main',
              '&:hover': {
                bgcolor: selectedEvent ? getTypeStyles(selectedEvent.place).hoverColor : 'primary.dark',
              }
            }}
          >
            Edit
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TimelineView;