import { VStack, HStack, Box, Button, Text, Image, Input, Center } from "@chakra-ui/react";
import { useState } from "react";

const Detector = () => {
    const [selectedImage, setSelectedImage] = useState(null);
    const [selectedImageFile, setSelectedImageFile] = useState(null);
    const [furcationImage, setFurcationImage] = useState(null);
    const [boneLossImage, setBoneLossImage] = useState(null);
    const [result, setResult] = useState("");

    const handleImageUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedImage(URL.createObjectURL(file)); // Preview image
            setSelectedImageFile(file); // Store actual file for upload
        }
    };

    const handleSubmit = async () => {
        if (!selectedImageFile) return;

        const formData = new FormData();
        formData.append("file", selectedImageFile);

        try {
            const response = await fetch("http://127.0.0.1:8000/predict", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (data.error) {
                console.error("Error:", data.error);
                return;
            }

            setResult(data.prediction);
            setFurcationImage("http://127.0.0.1:8000" + data.furcation_marker_url + "?t=" + Date.now());
            setBoneLossImage("http://127.0.0.1:8000" + data.bone_loss_image_url + "?t=" + Date.now());

        } catch (error) {
            console.error("Error fetching prediction:", error);
        }
    };

    return (
        <VStack spacing={2} p={2} bg="gray.200" minH="100vh" justify="center">
            <HStack spacing={300} p={5} bg="gray.400" w="full" justify="center" borderRadius="md">
                <VStack spacing={5}>
                    <Center w={400} h={170} borderRadius="lg" borderWidth={2} borderColor="gray.400" bg="white" cursor="pointer" textAlign="center">
                        <Input type="file" opacity={0} position="absolute" onChange={handleImageUpload} />
                        <Text>Upload an image</Text>
                    </Center>
                    <Button colorScheme="green" onClick={handleSubmit}>Submit</Button>
                </VStack>
                <Box bg="white" w={500} h={250} display="flex" alignItems="center" justifyContent="center" borderRadius="lg">
                    {selectedImage && <Image src={selectedImage} boxSize="100%" objectFit="contain" borderRadius="lg" />}
                </Box>
            </HStack>

            <Text fontSize="lg" fontWeight="bold">Result</Text>
            <Input value={result} isReadOnly w={300} textAlign="center" />

            <HStack spacing={200} w="full" justify="center">
                <VStack>
                    <Box w={500} h={250} bg="white" display="flex" alignItems="center" justifyContent="center" borderRadius="lg">
                        {furcationImage && <Image src={furcationImage} boxSize="100%" objectFit="contain" borderRadius="lg" />}
                    </Box>
                    <Text>Furcation</Text>
                </VStack>
                <VStack>
                    <Box w={500} h={250} bg="white" display="flex" alignItems="center" justifyContent="center" borderRadius="lg">
                        {boneLossImage && <Image src={boneLossImage} boxSize="100%" objectFit="contain" borderRadius="lg" />}
                    </Box>
                    <Text>Bone-Loss</Text>
                </VStack>
            </HStack>
        </VStack>
    );
};

export default Detector;
