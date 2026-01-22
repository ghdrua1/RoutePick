import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Philosophy from './components/Philosophy';
import Footer from './components/Footer';
import TripPlanner from './components/TripPlanner';

export default function App() {
  const [isPlannerOpen, setIsPlannerOpen] = useState(false);

  const openPlanner = () => setIsPlannerOpen(true);
  const closePlanner = () => setIsPlannerOpen(false);

  return (
    <main className="w-full min-h-screen relative overflow-hidden">
      <Navbar onPlanClick={openPlanner} />
      <Hero onPlanClick={openPlanner} />
      <Philosophy />
      <Footer />
      
      <TripPlanner isOpen={isPlannerOpen} onClose={closePlanner} />
    </main>
  );
}