import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  Stepper,
  Step,
  StepLabel,
  Typography,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import FilterListIcon from '@mui/icons-material/FilterList';
import TuneIcon from '@mui/icons-material/Tune';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

const tourSteps = [
  {
    target: '.place-card',
    title: '浏览地点',
    content: '这里展示了所有可选择的地点。您可以查看每个地点的详细信息、评分、价格和类型等。点击卡片可以查看更多详情。',
    placement: 'bottom'
  },
  {
    target: '.add-button',
    title: '添加到行程',
    content: '点击右上角的"+"按钮将感兴趣的地点添加到您的行程中。选中的地点会显示绿色对勾。',
    placement: 'left'
  },
  {
    target: '.search-filter',
    title: '搜索和筛选',
    content: '使用搜索栏查找特定地点，或使用筛选器按评分、价格和类型等条件筛选。',
    placement: 'bottom'
  },
  {
    target: '.sidebar-toggle',
    title: '查看已选地点',
    content: '点击左侧边栏按钮查看已添加到行程的地点。您可以在这里管理已选择的地点。',
    placement: 'right'
  },
  {
    target: '.proceed-button',
    title: '继续规划',
    content: '选择完心仪的地点后，点击"继续规划"进入下一步，开始安排您的行程。',
    placement: 'bottom'
  }
];

const PageTour = () => {
  const [open, setOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [showTourAgain, setShowTourAgain] = useState(true);

  useEffect(() => {
    const hasSeenTour = localStorage.getItem('hasSeenTour');
    if (!hasSeenTour && showTourAgain) {
      setOpen(true);
      localStorage.setItem('hasSeenTour', 'true');
    }
  }, [showTourAgain]);

  const handleClose = () => {
    setOpen(false);
    setActiveStep(0);
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSkip = () => {
    setShowTourAgain(false);
    handleClose();
  };

  return (
    <Dialog
      open={open}
      maxWidth="sm"
      fullWidth
      onClose={handleClose}
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxWidth: 500
        }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">欢迎使用地点选择</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Stepper activeStep={activeStep} orientation="vertical">
          {tourSteps.map((step, index) => (
            <Step key={index}>
              <StepLabel>
                <Typography variant="subtitle1" fontWeight="bold">
                  {step.title}
                </Typography>
              </StepLabel>
              {activeStep === index && (
                <Box sx={{ mt: 2, mb: 3 }}>
                  <DialogContentText>{step.content}</DialogContentText>
                </Box>
              )}
            </Step>
          ))}
        </Stepper>
      </DialogContent>
      <DialogActions sx={{ p: 2, pt: 0 }}>
        <Button onClick={handleSkip} color="inherit">
          不再显示
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        <Button onClick={handleBack} disabled={activeStep === 0}>
          上一步
        </Button>
        {activeStep === tourSteps.length - 1 ? (
          <Button onClick={handleClose} variant="contained">
            完成
          </Button>
        ) : (
          <Button onClick={handleNext} variant="contained">
            下一步
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PageTour;