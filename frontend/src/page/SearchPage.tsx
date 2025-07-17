import Button from "../components/Button";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import ColorChangingSpinner from "../components/Loader";
import { GoBookmark } from "react-icons/go";
import { MdEditNote } from "react-icons/md";
import { removeSpacePattern } from "../utils/spaceUtils";


interface Props {
    Quote: string;
}



export default function SearchPage({ Quote }: Props) {
    const Navigate = useNavigate();
    const [query, setQuery] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isError, setisError] = useState<boolean>(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const [activeTab, setActiveTab] = useState("All");
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [showSuggestion, setShowSuggestion] = useState(true);

    // const tabs = ["All", "Bookmarks", "Notes"];

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowSuggestion(false);
        }, 3500);

        return () => clearTimeout(timer);
    }, []);

    const handleSearch = () => {
        setIsLoading(true);
        chrome.runtime.sendMessage({ action: "search", query: query, type: activeTab },
            (response) => {
                setIsLoading(false);
                
                if (response && response.success) {
                    if (response.data?.detail === "Search failed: No documents found matching query") {
                        Navigate("/response", { state: { data: [] } });
                        return;
                    } else {
                        console.log("The response is:", response.data);
                        const responseArray = response.data.map((item: any) => ({
                            title: item.metadata.title,
                            url: item.metadata.source_url,
                            content: removeSpacePattern(item.metadata.note),
                            date: item.metadata.date,
                            ID: item.metadata.doc_id,
                            type: item.metadata.type
                        }));
                        Navigate("/response", { state: { data: responseArray, Query: query } });
                    }
                } else {
                    console.error("Search error:", response?.error);
                    const errorMessage = response?.error || "Search failed";
                    
                    if (errorMessage.includes("No documents found matching query")) {
                        Navigate("/response", { state: { data: [], Query: query } });
                    } else {
                        Navigate("/response", { state: { data: [], Query: query, error: errorMessage } });
                    }
                }
            }
        )
    };
    const handleSearchAll = () => {
        setIsLoading(true);
        chrome.runtime.sendMessage({ action: "searchAll" },
            (response) => {
                setIsLoading(false);
                
                if (response && response.success) {
                    if (response.data?.detail === "Search failed: No documents found matching query") {
                        console.log("No documents found matching query");
                        Navigate("/response", { state: { data: [] } });
                        return;
                    } else {
                        const linksArray = response.links.map((item: any) => ({
                            title: item.title,
                            url: item.source_url,
                            content: removeSpacePattern(item.note),
                            date: item.date,
                            ID: item.doc_id,
                            type: item.type
                        }));
                        const notesArray = response.notes.map((item: any) => ({
                            title: item.title,
                            content: removeSpacePattern(item.note),
                            date: item.date,
                            ID: item.doc_id,
                            type: item.type
                        }));
                        console.log("The links array is from search all: ", linksArray);
                        console.log("The notes array is from search all:", notesArray);
                        const responseArray = [...linksArray, ...notesArray];
                        Navigate("/response", { state: {data: responseArray, Query: " ", isSearchAll:true} });
                    }
                } else {
                    console.error("SearchAll Error:", response?.error);
                    
                    // Enhanced authentication error detection
                    const errorMessage = response?.error || '';
                    const isAuthError = (
                        errorMessage.includes('Authentication required') ||
                        errorMessage.includes('authentication failed') ||
                        errorMessage.includes('fetch failed: 401') ||
                        errorMessage.includes('401') ||
                        errorMessage.includes('Session expired') ||
                        errorMessage.includes('Please log in again') ||
                        errorMessage.includes('Invalid Refresh Token')
                    );
                    
                    if (isAuthError) {
                        console.log("🚫 SEARCH: Authentication error detected, redirecting to intro page");
                        Navigate("/");
                        return;
                    }
                    
                    // Handle other errors
                    Navigate("/response", { 
                        state: { 
                            data: [], 
                            Query: " ", 
                            isSearchAll: true, 
                            error: response?.error || "Failed to fetch data" 
                        } 
                    });
                }
            }
        )

    };




    return (
        <>

                <div className="max-w-md bg-white rounded-lg px-10 w-[420px] h-[500px] flex flex-col  justify-between py-10 border border-black">
                    <div className=" flex flex-col gap-2 ">
                    <div className="relative flex border-black border-[1.5px] rounded-full px-1 py-1 justify-between min-h-[43px]
                font-SansText400">
                        
                        {/* Conditionally render either the search input OR the filter options */}
                        {!isFilterOpen ? (
                            // Search Input State
                            <>
                                <input
                                    ref={inputRef}
                                    type="text"
                                    placeholder={`SEARCH ${activeTab==="All" ? "BOOKMARKS & NOTES" : activeTab.toLocaleUpperCase()} - PRESS ENTER`}
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                            if (query.length < 3) {
                                                setisError(true)
                                            }
                                            else {
                                                handleSearch();
                                            }
                                        }
                                    }}
                                    className="bg-transparent focus:outline-none text-black placeholder:text-[11px] placeholder:text-black flex-grow
                                    font-SansText400 pb-[1px] placeholder:tracking-widest
                                    placeholdder-opacity-25 transition-all duration-300 ease-in-out"
                                />

                                {isLoading ? (
                                    <div>
                                        <ColorChangingSpinner />
                                    </div>
                                ) : (
                                    <div className="relative">
                                        <button
                                            onClick={() => setIsFilterOpen(!isFilterOpen)}
                                            className="bg-black h-full rounded-full">
                                            {activeTab === "All" && <p className="text-white px-2 py-1 font-SansText400 tracking-widest">ALL</p>}
                                            {activeTab === "Bookmark" && <GoBookmark size={18} color="white" className="w-[32px]"/>}
                                            {activeTab === "Note" && <MdEditNote size={18} color="white" className="w-[32px]" />}
                                        </button>

                                        {showSuggestion && (
                                            <motion.div
                                                initial={{ opacity: 0, y: -10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -10 }}
                                                transition={{ duration: 0.3 }}
                                                className="absolute bg-[#dcdcdc] text-black right-0 top-[50px] px-4 py-2 rounded-full text-[10px] font-SansText400 tracking-wider whitespace-nowrap z-10"
                                            >
                                                click here to filter
                                                <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-[#dcdcdc] rotate-45"></div>
                                            </motion.div>
                                        )}
                                    </div>
                                )}
                            </>
                        ) : (
                            // Filter Selection State
                            <motion.div
                                initial={{ opacity: 0, x: 50 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 50 }}
                                transition={{ duration: 0.3, ease: "spring" }}
                                className="flex justify-center items-center w-full h-full gap-2 font-SansText400 tracking-widest"
                            >
                                <button 
                                    onClick={() => {setActiveTab("All"); setIsFilterOpen(false);}}
                                    className={`${activeTab === "All" ? "bg-lime-300 px-4 py-2 text-gray-800 shadow-sm" : "text-gray-600 hover:text-gray-800 px-2 py-1"} rounded-full transition-all duration-200`}
                                >
                                    ALL
                                </button>
                                <button
                                    onClick={() => {setActiveTab("Bookmark"); setIsFilterOpen(false);}}
                                    className={`${activeTab === "Bookmark" ? "bg-lime-300 px-4 py-2 text-gray-800 shadow-sm" : "text-gray-600 hover:text-gray-800 px-2 py-1"} rounded-full transition-all duration-200`}
                                >
                                    BOOKMARKS
                                </button>
                                <button
                                    onClick={() => {setActiveTab("Note"); setIsFilterOpen(false);}}
                                    className={`${activeTab === "Note" ? "bg-lime-300 px-4 py-2 text-gray-800 shadow-sm" : "text-gray-600 hover:text-gray-800 px-2 py-1"} rounded-full transition-all duration-200`}
                                >
                                    NOTES
                                </button>
                            </motion.div>
                        )}
                    </div>
                </div>

                <div className={`font-NanumMyeongjo  text-4xl text-center ${isError ? "text-red-900" : "text-black"}`}>
                    <motion.h1
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 1.5 }}
                        className="text-center"
                    >"{isError ? "The Query must be atleast 3 characters !" : Quote}"</motion.h1>
                </div>
                <div className="w-[95%] mx-auto flex justify-between items-center">
                    <Button text="HOME" handle={() => Navigate("/submit")} textColor="--primary-white"
                        IncMinWidth="118px" />
                    <Button 
                        text={query.trim() ? "SEARCH" : "SHOW ALL"} 
                        handle={query.trim() ? handleSearch : handleSearchAll} 
                        textColor="--primary-white" 
                    />
                </div>
            </div>
        </>
    );
}