import React from 'react';
import { ArrowRight } from 'lucide-react';

const Cta: React.FC = () => {
  return (
    <section className="bg-[#EBEBE9] py-24 md:py-32 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex flex-col md:flex-row items-end justify-between gap-12">
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-widest text-gray-500 mb-4">Newsletter</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-8 leading-tight">
            New RoutePick production updates, travel stories, and secret destinations found in the wild — find it in our newsletter.
          </h2>
          
          <div className="relative max-w-md">
            <input 
              type="email" 
              placeholder="name@email.com" 
              className="w-full bg-white border-none rounded-full py-4 pl-6 pr-32 focus:ring-1 focus:ring-black outline-none placeholder-gray-400"
            />
            <button className="absolute right-1 top-1 bottom-1 bg-black text-white px-6 rounded-full text-sm font-medium hover:bg-gray-800 transition-colors flex items-center gap-2">
              Register <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="w-full md:w-1/3 aspect-video rounded-xl overflow-hidden shadow-lg relative group cursor-pointer">
            <img 
                src="https://picsum.photos/seed/van_life/800/600" 
                alt="Travel Lifestyle" 
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
            />
            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors"></div>
            <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider">
                Watch Film
            </div>
        </div>
      </div>
    </section>
  );
};

export default Cta;