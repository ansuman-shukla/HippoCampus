
export default function ToggleTabs({activeTab,setActiveTab,tabs}:{activeTab:string, setActiveTab:(tab:string) => void,tabs:string[]}) {
  

  return (
    <div className="flex justify-center items-center">
        <div className="fixed top-3 z-[99999] bg-white drop-shadow-2xl flex border-[1.5px] border-black  rounded-full p-0.5 space-x-2 max-h-[43px]">
            {tabs.map((tab) => (
                <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 py-[8px] rounded-full transition-all duration-300 ease-in-out
                        ext-black text-[10px] font-SansText400  tracking-widest
                        ${
                        activeTab === tab
                            ? "bg-lime-300 text-gray-800 shadow-sm"
                            : "text-gray-600 hover:text-gray-800 "
                    }`}
                >
                    {tab !== "All" ? tab.toUpperCase() + "S"  : "ALL"}
                </button>
            ))}
        </div>
    </div>
  );
}