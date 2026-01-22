import React from 'react';

const Gallery: React.FC = () => {
  return (
    <section className="relative w-full py-24 md:py-32 bg-white overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        {/* Subtle grid pattern */}
        <div className="w-full h-full opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
                 <h2 className="text-5xl md:text-7xl font-bold tracking-tighter leading-none mb-8">
                    More to <br/>
                    <span className="font-serif italic text-gray-500">Discover</span>
                </h2>
                <p className="text-gray-600 mb-12 max-w-md">
                    From the winding coasts of Amalfi to the silent peaks of the Andes, RoutePick curates experiences that resonate with your soul.
                </p>
                
                <div className="space-y-8">
                     <div className="border-t border-gray-200 pt-6">
                        <span className="text-xs text-gray-400 uppercase tracking-widest mb-2 block">09.16.2025</span>
                        <h3 className="text-xl font-medium hover:text-gray-600 cursor-pointer transition-colors">Why I chose an AI Curator over a Travel Agent</h3>
                     </div>
                     <div className="border-t border-gray-200 pt-6">
                        <span className="text-xs text-gray-400 uppercase tracking-widest mb-2 block">10.29.2025</span>
                        <h3 className="text-xl font-medium hover:text-gray-600 cursor-pointer transition-colors">The Future of Sustainable Tourism</h3>
                     </div>
                     <div className="border-t border-gray-200 pt-6">
                        <span className="text-xs text-gray-400 uppercase tracking-widest mb-2 block">06.13.2025</span>
                        <h3 className="text-xl font-medium hover:text-gray-600 cursor-pointer transition-colors">Hidden Gems: The Algorithm's Secret Spots</h3>
                     </div>
                </div>
            </div>

            <div className="relative h-[600px] w-full">
                <div className="absolute top-0 right-0 w-4/5 h-3/5 overflow-hidden rounded-lg shadow-2xl z-10">
                    <img src="https://picsum.photos/seed/mountain_hike/800/1000" alt="Mountain" className="w-full h-full object-cover hover:scale-105 transition-transform duration-1000" />
                </div>
                 <div className="absolute bottom-0 left-0 w-3/5 h-1/2 overflow-hidden rounded-lg shadow-2xl z-20">
                    <img src="https://picsum.photos/seed/ocean_view/600/800" alt="Ocean" className="w-full h-full object-cover hover:scale-105 transition-transform duration-1000" />
                </div>
            </div>
        </div>
      </div>
    </section>
  );
};

export default Gallery;