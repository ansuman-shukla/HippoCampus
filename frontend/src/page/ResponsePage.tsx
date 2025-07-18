import { useNavigate } from "react-router-dom";
import InputForm from "../components/InputForm";
import { useEffect, useState, useRef } from "react";
import { BiSearchAlt2 } from "react-icons/bi";
import '../index.css';
import isUrlHttp from "is-url-http";

interface FormData {
  link: string;
  title: string;
  note: string;
}

export default function ResponsePage() {

  const [title, setTitle] = useState("Good Morning");
  const [subTxt, setSubTxt] = useState("User");
  const [leftBtnTxt, setLftBtnTxt] = useState("SUMMARIZE");
  const [BtnTxtClr, setBtnTxtClr] = useState("--primary-yellow");
  const [rightBtnTxt, setRtBtnTxt] = useState("MEMORIZE");
  const [notSubmitted, setnotSubmitted] = useState(true);
  const [bgClr, setbgClr] = useState("--primary-yellow");
  const [isError, setisError] = useState('');
  const [showOnlyOne, setShowOnlyOne] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTab, setCurrentTab] = useState("submit");
  const [extraNote, setExtraNote] = useState("");
  const [NotesTitle, setNotesTitle] = useState("");

  const Navigate = useNavigate();
  const [DoneNumber, setDoneNumber] = useState(0);
  const isNavigating = useRef(false);

  function isValidURL(url:string) {
        console.log("The url is:", url ,"and it is valid", isUrlHttp(url));
        return !isUrlHttp(url);
  }


  useEffect(() => {
    if(new Date().getHours()<5){
      setTitle("Go & Sleep,");
    }
    else if( new Date().getHours() < 12){
      setTitle("Good Morning,")
    }else if(new Date().getHours() < 17){
      setTitle("Good Afternoon,")
    }else if( new Date().getHours() < 20){
      setTitle("Good Evening,")
    }else{
      setTitle("Good Night,")
    } 
  }, []);

  useEffect(() => {
    // First check localStorage for cached username
    const cachedUsername = localStorage.getItem('user_name');
    
    if (cachedUsername) {
      // Process cached username to ensure it follows the same rules (first name, max 8 chars)
      const firstName = cachedUsername.split(" ")[0];
      const processedUsername = firstName.length > 8 ? firstName.substring(0, 8) : firstName;
      
      console.log('Using cached username from localStorage:', processedUsername);
      setSubTxt(processedUsername);
      
      // Update localStorage if the cached value was different (full name)
      if (processedUsername !== cachedUsername) {
        localStorage.setItem('user_name', processedUsername);
        console.log('Updated cached username to processed version');
      }
    } else {
      // If not in localStorage, fetch from cookies (existing logic)
      console.log('Username not found in localStorage, fetching from cookies...');
      chrome.cookies.get({url: import.meta.env.VITE_BACKEND_URL, name:'user_name'},(cookie)=>{
        if(cookie){
          // Extract first name and truncate to 8 characters if needed
          const fullName = cookie.value.replace(/"/g, "");
          const firstName = fullName.split(" ")[0];
          const username = firstName.length > 8 ? firstName.substring(0, 8) : firstName;
          
          console.log('Username processed from cookies:', username);
          
          // Set the username in the UI
          setSubTxt(username);
          
          // Cache it in localStorage for future use
          localStorage.setItem('user_name', username);
          console.log('Username cached in localStorage for future use');
        } else {
          console.log('No username found in cookies, trying to fetch auth status');
          // As a fallback, try to get auth status which should populate localStorage
          fetch(`${import.meta.env.VITE_BACKEND_URL}/auth/status`, {
            method: 'GET',
            credentials: 'include',
          })
            .then(response => response.json())
            .then(data => {
              if (data.is_authenticated && data.full_name) {
                const firstName = data.full_name.split(" ")[0];
                const username = firstName.length > 8 ? firstName.substring(0, 8) : firstName;
                setSubTxt(username);
                localStorage.setItem('user_name', username);
                console.log('Username fetched from auth status and cached');
              }
            })
            .catch(error => {
              console.log('Failed to fetch auth status:', error);
            });
        }
      });
    }
  }, []);




  const [formData, setFormData] = useState<FormData>({
    link: '',
    title: '',
    note: ''
  });
  const getLink = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      setFormData({ ...formData, link: tabs[0].url || '', title: tabs[0].title || '' })
    })
  }
  if (formData.link == "" && DoneNumber == 0) {
    getLink();
    setDoneNumber(1);
  }



  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };


  const handleResponse = (e: React.FormEvent) => {
    e.preventDefault();


    if (currentTab === "submit" && (formData.link === "" || isValidURL(formData.link) || formData.title === "")) {
      setnotSubmitted(true);
      if(isValidURL(formData.link)){
        setisError("Enter a valid link!")
        return
      }
      setisError("Link or Title missing!")
      return
    }
    else if (currentTab === "notes" && (NotesTitle.trim() === "" || extraNote.trim() === "")) {
      setnotSubmitted(true);
      setisError("Title and Note are required!")
      return
    }
    else {
      setIsLoading(true);
      setisError('')
      setnotSubmitted(false);

     (currentTab === "submit" ? chrome.runtime.sendMessage({ action: "submit", data: formData }, (response) => {
        console.log("Frontend received response:", response);
        if (response && response.success) {
          setIsLoading(false);
          setbgClr("--primary-green")
          setTitle("Successful !")
          setSubTxt("Your entry has been saved.")
          setLftBtnTxt("CLOSE")
          setBtnTxtClr("--primary-green")
          setRtBtnTxt("HOME")
          setShowOnlyOne(true)
        } else {
          setIsLoading(false);
          console.error("API Error:", response);
          setbgClr("--primary-orange")
          setTitle("Error !")
          setSubTxt("Something went wrong")
          setLftBtnTxt("Home")
          setBtnTxtClr("--primary-orange")
          setRtBtnTxt("RETRY :)")
          setisError("API Error")
        }
      }) : (
        chrome.runtime.sendMessage({ action: "saveNotes", data: {
          title: NotesTitle,
          note: extraNote
        } }, (response) => {
          console.log("Frontend received saveNotes response:", response);
          if (response && response.success) {
            setIsLoading(false);
            setbgClr("--primary-green")
            setTitle("Successful !")
            setSubTxt("Your notes has been saved.")
            setLftBtnTxt("CLOSE")
            setBtnTxtClr("--primary-green")
            setRtBtnTxt("HOME")
            setShowOnlyOne(true)
          } else {
            setIsLoading(false);
            console.error("API Error:", response);
            setbgClr("--primary-orange")
            setTitle("Error !")
            setSubTxt("Something went wrong")
            setLftBtnTxt("BACK")
            setBtnTxtClr("--primary-orange")
            setRtBtnTxt("RETRY :)")
            setisError("API Error")
          }
        })
      )
    
     )

    }


  }

  const handleClear = () => {
    // Prevent multiple rapid clicks/navigation
    if (isNavigating.current) {
      return;
    }
    
    if (showOnlyOne && leftBtnTxt == "CLOSE") {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tabId = tabs[0].id;
        if(tabId){
          chrome.tabs.sendMessage(tabId, { 
            action: "closeExtension",
            target: "content"
          }, () => {
          });
        }
      });
    } else if (leftBtnTxt === 'Home') {
      Navigate(0);
    }
    else{
      // Set navigation flag and navigate to summarize
      isNavigating.current = true;
      Navigate("/summarize");
      
      // Reset flag after a delay to allow for normal navigation
      setTimeout(() => {
        isNavigating.current = false;
      }, 1000);
    }
  };

  return (
    <>

      <div className={`max-w-md bg-[var(${bgClr})] rounded-lg px-9 w-[420px] h-[500px] flex flex-col justify-between py-10
      border border-black`}>


        <div className="flex justify-between items-center mb-6 gap-2 ">
          <div className='flex flex-col justify-end  -gap-2'>
            <h1 className="text-[18px] font-NanumMyeongjo pr-2">{title}</h1>
            <p className={`${(subTxt==="Your entry has been saved." || subTxt==="Something went wrong")?'text-[24px]':'text-[28px]'} text-black font-NanumMyeongjo mt-[-8px]`}>{subTxt}</p>
          </div>
          {notSubmitted ?
            <div
              className="group relative flex items-center cursor-pointer box-border bg-transparent 
             px-2 py-2 rounded-full "
              onClick={() => Navigate("/search")}
            >
              <input
                type="text"
                placeholder="SEARCH"
                className="bg-transparent focus:outline-none text-black placeholder:text-[11px] 
              placeholder:text-black w-[70px] font-SansText400 pb-[2px] 
              placeholder:tracking-widest cursor-pointer relative z-10"
              />
              <BiSearchAlt2 size={24} className="relative z-10" />

              {/* Animated border element */}
              <div className="absolute inset-0 before:absolute before:inset-0 before:border-[1.5px] 
                before:border-black before:rounded-full before:scale-100 
                before:transition-transform before:duration-300 before:ease-in-out 
                group-hover:before:scale-105 group-hover:before:border-2">
              </div>
            </div>

            : null}
        </div>


        <InputForm
          handleChange={handleChange}
          handleClear={handleClear}
          handleSubmit={handleResponse}
          formData={formData}
          BtnTxtClr={BtnTxtClr}
          leftBtnTxt={leftBtnTxt}
          rightBtnTxt={rightBtnTxt}
          Error={isError}
          showOnlyOne={showOnlyOne}
          isLoading={isLoading}
          currentTab={currentTab}
          setCurrentTab={setCurrentTab}
          extraNote={extraNote}
          setExtraNote={setExtraNote}
          NotesTitle={NotesTitle}
          setNotesTitle={setNotesTitle}
        />
        
      </div>
    </>
  );
}