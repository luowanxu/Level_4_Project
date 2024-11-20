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
    title: 'Browse Places',
    content: 'Here you can view all available places. Check details like ratings, prices, and categories. Click on a card to see more information.',
    placement: 'bottom'
  },
  {
    target: '.add-button',
    title: 'Add to Itinerary',
    content: 'Click the "+" button in the top right corner to add places to your itinerary. Selected places will show a green checkmark.',
    placement: 'left'
  },
  {
    target: '.search-filter',
    title: 'Search & Filter',
    content: 'Use the search bar to find specific places, or use filters to sort by rating, price, and categories.',
    placement: 'bottom'
  },
  {
    target: '.sidebar-toggle',
    title: 'View Selected Places',
    content: 'Click the sidebar button to view places added to your itinerary. You can manage your selections here.',
    placement: 'right'
  },
  {
    target: '.proceed-button',
    title: 'Continue Planning',
    content: 'After selecting your desired places, click "Proceed to Planning" to move on and arrange your itinerary.',
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
          <Typography variant="h6">Welcome to Place Selection</Typography>
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
          Don't show again
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        <Button onClick={handleBack} disabled={activeStep === 0}>
          Back
        </Button>
        {activeStep === tourSteps.length - 1 ? (
          <Button onClick={handleClose} variant="contained">
            Finish
          </Button>
        ) : (
          <Button onClick={handleNext} variant="contained">
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PageTour;