import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';

interface NavbarProps {
  onPlanClick: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onPlanClick }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav 
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-in-out px-6 md:px-12 py-4 bg-white/90 backdrop-blur-md border-b border-gray-200"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="text-2xl font-serif font-bold tracking-tight text-route-black">
          RoutePick
        </div>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center space-x-8 text-sm font-medium uppercase tracking-widest text-route-black">
          {/* Links removed as requested */}
          <button 
            onClick={onPlanClick}
            className="px-5 py-2 rounded-full border border-black transition-all hover:bg-black hover:text-white cursor-pointer"
          >
            Plan Trip
          </button>
        </div>

        {/* Mobile Toggle */}
        <button 
          className="md:hidden" 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X className="text-black" /> : <Menu className="text-black" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="absolute top-full left-0 w-full bg-white text-black py-8 px-6 shadow-xl flex flex-col space-y-6 md:hidden">
          <button 
            onClick={() => {
              setIsMobileMenuOpen(false);
              onPlanClick();
            }}
            className="w-full py-3 bg-black text-white rounded-full"
          >
            Plan Trip
          </button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;