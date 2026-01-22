import React from 'react';
import { Github, Map, Navigation } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white py-12 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8 md:gap-0">
            {/* Left: Brand */}
            <div className="flex items-center">
               <span className="font-serif font-bold text-2xl tracking-tight">RoutePick</span>
            </div>
            
            {/* Center: Icons */}
            <div className="flex items-center space-x-12">
                <Navigation className="w-8 h-8 text-black" />
                <Map className="w-8 h-8 text-black" />
            </div>

            {/* Right: Github */}
            <div className="flex items-center">
                <a 
                  href="https://github.com/yunjin-Kim4809/RoutePick" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                  aria-label="GitHub"
                >
                    <Github className="w-6 h-6 text-black" />
                </a>
            </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;