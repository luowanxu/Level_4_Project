// OptimizedTimelineView.js
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  useTheme,
  useMediaQuery,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Snackbar,
  SpeedDial,
  SpeedDialIcon,
  SpeedDialAction,
  CircularProgress,
} from '@mui/material';
import {
    DragIndicator as DragIcon,
    AccessTime as TimeIcon,
    Place as PlaceIcon,
    Autorenew as AutorenewIcon,
    EditOff as EditOffIcon,
    DirectionsWalk,
    DirectionsCar,
    DirectionsTransit,
  } from '@mui/icons-material';
import { Rnd } from 'react-rnd';
import axios from 'axios';


const MIN_TIMELINE_WIDTH = 1200;  // 最小宽度
const HOUR_WIDTH = 100;           // 每小时的宽度
const EXTRA_SPACE = 200;          // 添加额外空间，等于事件块宽度
const MINUTES_PER_HOUR = 60;
const DAY_START_HOUR = 9;  // 9:00 AM
const DAY_END_HOUR = 21;   // 9:00 PM
const TOTAL_HOURS = DAY_END_HOUR - DAY_START_HOUR;



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


  // 修改时间转换函数
const timeToMinutes = (timeString) => {
  // 处理24小时制的输入
  if (!timeString.includes('AM') && !timeString.includes('PM')) {
    const [hours, minutes] = timeString.split(':').map(Number);
    return hours * 60 + minutes;
  }

  const [time, period] = timeString.split(' ');
  let [hours, minutes] = time.split(':').map(Number);
  if (period === 'PM' && hours !== 12) hours += 12;
  if (period === 'AM' && hours === 12) hours = 0;
  return hours * 60 + minutes;
};

// 统一使用12小时制转换时间
const to12HourFormat = (timeString) => {
  // 如果已经是12小时制，直接返回
  if (timeString.includes('AM') || timeString.includes('PM')) {
    return timeString;
  }

  const [hours, minutes] = timeString.split(':').map(Number);
  let period = 'AM';
  let displayHours = hours;

  if (hours >= 12) {
    period = 'PM';
    if (hours > 12) displayHours = hours - 12;
  }
  if (hours === 0) displayHours = 12;

  return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
};




  
  const minutesToTime = (totalMinutes) => {
    let hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    let period = 'AM';
    
    if (hours >= 12) {
      period = 'PM';
      if (hours > 12) hours -= 12;
    }
    if (hours === 0) hours = 12;
    
    return `${hours}:${minutes.toString().padStart(2, '0')} ${period}`;
  };





  const TIME_SCALE = {
    START_HOUR: 9,    // 9:00 AM
    END_HOUR: 21,     // 9:00 PM
    TOTAL_HOURS: 12,  // 12 hours
    MAJOR_STEPS: [9, 12, 15, 18, 21]  // 主要时间点
  };



const LEFT_SIDEBAR_WIDTH = 160;  // 左侧日期栏宽度

const OptimizedTimelineView = ({ startDate, endDate, selectedPlaces, onEventsUpdate, transportMode }) => {
  const [events, setEvents] = useState([]);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [timelineWidth, setTimelineWidth] = useState(0);
  const [isManualMode, setIsManualMode] = useState(false);
  const [showModeDialog, setShowModeDialog] = useState(false);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [draggingEventId, setDraggingEventId] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);





  const ModeChangeDialog = () => (
    <Dialog
      open={showModeDialog}
      onClose={() => setShowModeDialog(false)}
    >
      <DialogTitle>Switch to Manual Mode?</DialogTitle>
      <DialogContent>
        <Typography>
          You're about to switch to manual mode. This will allow you to:
          <ul>
            <li>Freely adjust event times</li>
            <li>Rearrange events between days</li>
            <li>Customize your schedule</li>
          </ul>
          The travel times between locations will be automatically recalculated.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowModeDialog(false)}>Cancel</Button>
        <Button 
          onClick={() => {
            setIsManualMode(true);
            setShowModeDialog(false);
            setShowSnackbar(true);
          }}
          variant="contained"
        >
          Switch to Manual
        </Button>
      </DialogActions>
    </Dialog>
  );


  const handleReoptimize = async () => {
    setIsOptimizing(true);
    try {
      const response = await axios.post('/api/cluster-places/', {
        places: events.filter(e => !e.type).map(e => e.place), // 只发送非交通事件
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        transportMode: transportMode
      });

      if (response.data.success) {
        onEventsUpdate(response.data.events);
        setIsManualMode(false);
        setShowSnackbar(true);
      }
    } catch (error) {
      console.error('Failed to reoptimize:', error);
    } finally {
      setIsOptimizing(false);
    }
  };







  
  // 计算时间轴的宽度（减去左侧栏的宽度和内边距）
  useEffect(() => {
    const updateWidth = () => {
      // 计算总小时数
      const totalHours = TIME_SCALE.TOTAL_HOURS;
      // 每小时固定宽度，加上额外空间
      const width = totalHours * HOUR_WIDTH + EXTRA_SPACE;
      // 确保不小于最小宽度
      setTimelineWidth(Math.max(width, MIN_TIMELINE_WIDTH));
    };
  
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // 计算日期范围
  const days = startDate && endDate ? 
    Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1 : 0;

  // 时间转像素
  // 修改 timeToPosition 函数
  // 修改时间位置转换函数
  const positionToTime = (x) => {
    // 计算从开始时间算起的分钟数
    const totalMinutes = (x / HOUR_WIDTH) * MINUTES_PER_HOUR;
    const hours = Math.floor(totalMinutes / MINUTES_PER_HOUR) + DAY_START_HOUR;
    const minutes = Math.floor(totalMinutes % MINUTES_PER_HOUR);
    
    // 转换为12小时制
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours > 12 ? hours - 12 : (hours === 0 ? 12 : hours);
    
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
  };
  
  // 将时间转换为位置
  const timeToPosition = (timeString) => {
    const [time, period] = timeString.split(' ');
    let [hours, minutes] = time.split(':').map(Number);
    if (period === 'PM' && hours !== 12) hours += 12;
    if (period === 'AM' && hours === 12) hours = 0;
    
    const hourPosition = (hours - TIME_SCALE.START_HOUR) * HOUR_WIDTH;
    const minutePosition = (minutes / 60) * HOUR_WIDTH;
    return hourPosition + minutePosition;
  };
  
  // 修改拖拽开始处理
  const handleDragStart = (eventId) => {
    if (!isManualMode) {
      setShowModeDialog(true);
    }
  };
  
  const handleDragStop = (eventId) => (e, d) => {
    if (!isManualMode) return;
  
    const event = events.find(e => e.id === eventId);
    const duration = event.place?.types?.includes('restaurant') ? 90 : 120;
  
    // 计算新位置的结束时间
    const newStartTime = positionToTime(d.x);
    const startMinutes = timeToMinutes(newStartTime);
    const endMinutes = startMinutes + duration;
    const maxEndHour = 21; // 9 PM
  
    // 检查是否超出有效时间范围
    if (endMinutes/60 <= maxEndHour) {
      // 在有效范围内才更新位置
      const newDay = Math.floor(d.y / 100);
      const newEndTime = minutesToTime(endMinutes);
  
      setEvents(prev => prev.map(evt => {
        if (evt.id === eventId) {
          return {
            ...evt,
            startTime: newStartTime,
            endTime: newEndTime,
            day: newDay
          };
        }
        return evt;
      }));
    }
    // 如果超出范围，不更新状态，事件块会自动回到上一个位置
  };



  const to12HourFormat = (timeString) => {
    // 如果已经是12小时制，直接返回
    if (timeString.includes('AM') || timeString.includes('PM')) {
      return timeString;
    }
  
    // 处理24小时制
    const [hours, minutes] = timeString.split(':').map(Number);
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours > 12 ? hours - 12 : (hours === 0 ? 12 : hours);
    
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
  };

  



  const TransportIcon = ({ mode, ...props }) => {
    switch (mode) {
      case 'walking':
        return <DirectionsWalk {...props} />;
      case 'driving':
        return <DirectionsCar {...props} />;
      case 'transit':
        return <DirectionsTransit {...props} />;
      default:
        return <DirectionsWalk {...props} />;
    }
  };



  // 在初始化事件时统一格式
const initializeEvents = (rawEvents) => {
  return rawEvents.map(event => ({
    ...event,
    startTime: to12HourFormat(event.startTime),
    endTime: to12HourFormat(event.endTime),
    position: {
      x: Math.min(timeToPosition(to12HourFormat(event.startTime)), timelineWidth - 200),
      y: event.day * 100
    }
  }));
};




useEffect(() => {
  const initializeTimeline = async () => {
    if (!startDate || !endDate || !selectedPlaces?.length) return;

    setLoading(true);
    try {
      const response = await axios.post('/api/cluster-places/', {
        places: selectedPlaces,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        transportMode: transportMode
      });

      if (response.data.success) {
        // 转换时间格式
        const formattedEvents = response.data.events.map(event => ({
          ...event,
          startTime: to12HourFormat(event.startTime),
          endTime: to12HourFormat(event.endTime)
        }));
        
        setEvents(formattedEvents);
        onEventsUpdate(formattedEvents);
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
}, [startDate, endDate, selectedPlaces, transportMode, onEventsUpdate]);




  return (
    <Box sx={{ position: 'relative', height: '100%' }}>
      <Box sx={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
        {/* 左侧日期栏 - 保持不变 */}
        <Box sx={{ 
          width: LEFT_SIDEBAR_WIDTH, 
          flexShrink: 0,
          borderRight: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper'
        }}>
        {/* 顶部占位 */}
        <Box sx={{ 
          height: 50, 
          borderBottom: 1, 
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          px: 2
        }}>
          <Typography variant="subtitle2" color="text.secondary">
            Schedule
          </Typography>
        </Box>
        
        {/* 日期列表 */}
        {Array.from({ length: days }).map((_, index) => {
          const currentDate = new Date(startDate);
          currentDate.setDate(startDate.getDate() + index);
          
          return (
            <Box
              key={index}
              sx={{
                height: 100,
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                px: 2
              }}
            >
              <Typography variant="subtitle1" color="primary">
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

      {/* 时间轴区域 */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'auto',
        position: 'relative'
      }}>
        <Box sx={{
          position: 'relative',
          width: `${timelineWidth}px`,
          minHeight: '100%',  // 改用 minHeight
          borderTop: 'none'   // 移除可能的边框
        }}>
          {/* 时间刻度 */}
          <Box sx={{
            height: 50,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            position: 'sticky',
            top: 0,
            bgcolor: 'background.paper',
            zIndex: 1,
            pl: 2  // 添加左侧padding
          }}>
            {TIME_SCALE.MAJOR_STEPS.map(hour => (
              <Typography
              key={hour}
              variant="body2"
              color="text.secondary"
              sx={{
                position: 'absolute',
                left: (hour - TIME_SCALE.START_HOUR) * HOUR_WIDTH + 40,  // +40是左侧padding
                transform: 'translateX(-50%)',
                whiteSpace: 'nowrap'
              }}
            >
                {hour > 12 ? `${hour-12}:00 PM` : `${hour}:00 ${hour === 12 ? 'PM' : 'AM'}`}
              </Typography>
            ))}
          </Box>

          {/* 事件区域 */}
          <Box sx={{ 
            position: 'relative', 
            height: '100%',
            overflow: 'hidden'  // 防止出现双滚动条
          }}>
            <Box sx={{ 
              display: 'flex', 
              height: '100%',
              overflow: 'hidden'
            }}>
              {/* 时间刻度 */}
              <Box sx={{
                height: 50,
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                position: 'sticky',
                top: 0,
                bgcolor: 'background.paper',
                zIndex: 1,
                pl: '40px'
              }}>
                {/* 时间刻度内容 */}
              </Box>
      
              {/* 事件区域 */}
              <Box sx={{ 
                position: 'relative',
                height: days * 100,
                width: '100%'
              }}>
                {events.map(event => (
                  event.type === 'transit' ? (
                    // 交通时间块
                    <Box
                      key={event.id}
                      sx={{
                        position: 'absolute',
                        left: timeToPosition(event.startTime),
                        top: event.day * 100,
                        width: 80,
                        height: 60,
                        zIndex: 1
                      }}
                    >
                      <Paper
                        elevation={1}
                        sx={{
                          height: '100%',
                          p: 1,
                          bgcolor: 'background.default',
                          border: '1px dashed',
                          borderColor: 'divider',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <TransportIcon 
                          mode={event.mode} 
                          sx={{ fontSize: 16, color: 'text.secondary' }} 
                        />
                        <Typography variant="caption" color="text.secondary">
                          {Math.round(event.duration / 60)} min
                        </Typography>
                      </Paper>
                    </Box>
                  ) : (
                    // 可拖动的事件块
                    <Rnd
                      key={event.id}
                      default={{
                        x: timeToPosition(event.startTime),
                        y: event.day * 100,
                        width: 200,
                        height: 80
                      }}
                      position={{
                        x: timeToPosition(event.startTime),
                        y: event.day * 100
                      }}
                      size={{
                        width: 200,
                        height: 80
                      }}
                      bounds="parent"
                      enableResizing={false}
                      onDragStart={handleDragStart}
                      onDragStop={(e, d) => handleDragStop(event.id)(e, d)}
                    >
                         {/* Paper 内容保持不变 */}
                      <Paper
                        elevation={3}
                        sx={{
                          height: '100%',
                          bgcolor: getTypeStyles(event.place).backgroundColor,
                          color: 'white',
                          p: 1,
                          display: 'flex',
                          alignItems: 'center',
                          '&:hover': {
                            bgcolor: getTypeStyles(event.place).hoverColor,
                          },
                        }}
                      >
                        <Box sx={{ 
                          flex: 1,
                          overflow: 'hidden',
                          minWidth: 0
                        }}>
                          <Typography variant="subtitle2" noWrap>
                            {event.title}
                          </Typography>
                          <Typography variant="caption" display="block" noWrap>
                            {event.startTime} - {event.endTime}
                          </Typography>
                          {event.place?.vicinity && (
                            <Typography variant="caption" display="block" noWrap color="rgba(255,255,255,0.8)">
                              {event.place.vicinity}
                            </Typography>
                          )}
                        </Box>
                      </Paper>
                    </Rnd>
                  )
                ))}
          </Box>
          </Box>
          </Box>
        </Box>
        </Box>

    {/* 2. 添加模式切换对话框 */}
    <Dialog
      open={showModeDialog}
      onClose={() => setShowModeDialog(false)}
    >
      <DialogTitle>Switch to Manual Mode?</DialogTitle>
      <DialogContent>
        <Typography>
          You're about to switch to manual mode. This will allow you to:
          <ul>
            <li>Freely adjust event times</li>
            <li>Rearrange events between days</li>
            <li>Customize your schedule</li>
          </ul>
          The travel times between locations will be automatically recalculated.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowModeDialog(false)}>
          Cancel
        </Button>
        <Button 
          variant="contained"
          onClick={() => {
            setIsManualMode(true);
            setShowModeDialog(false);
            setShowSnackbar(true);
          }}
        >
          Switch to Manual
        </Button>
      </DialogActions>
    </Dialog>

    {/* 3. 添加提示消息条 */}
    <Snackbar
      open={showSnackbar}
      autoHideDuration={4000}
      onClose={() => setShowSnackbar(false)}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
    >
      <Alert 
        onClose={() => setShowSnackbar(false)} 
        severity="info"
      >
        {isManualMode ? 
          'Switched to manual mode. You can now freely adjust events.' :
          'Schedule has been optimized for shortest travel times.'
        }
      </Alert>
    </Snackbar>

    {/* 4. 添加右下角的悬浮操作按钮 */}
    <SpeedDial
      ariaLabel="Schedule controls"
      sx={{ 
        position: 'absolute', 
        bottom: 16, 
        right: 16 
      }}
      icon={<SpeedDialIcon />}
    >
      <SpeedDialAction
        icon={isManualMode ? <AutorenewIcon /> : <EditOffIcon />}
        tooltipTitle={isManualMode ? "Reoptimize Schedule" : "Current Mode: Automatic"}
        onClick={isManualMode ? handleReoptimize : undefined}
        disabled={isOptimizing}
      />
    </SpeedDial>
  </Box>
  </Box>
);
};

export default OptimizedTimelineView;